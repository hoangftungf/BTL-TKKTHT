"""
AI Recommendation Engine
Sử dụng Collaborative Filtering và Content-Based Filtering
"""

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from scipy.sparse import csr_matrix
from django.conf import settings
from django.core.cache import cache
from django.db import models
import httpx
import logging

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Hybrid Recommendation Engine kết hợp:
    1. Collaborative Filtering (User-Item matrix)
    2. Content-Based Filtering (Product features)
    3. Popularity-Based (Trending)
    """

    INTERACTION_WEIGHTS = {
        'view': 1.0,
        'cart': 3.0,
        'wishlist': 2.0,
        'purchase': 5.0,
        'review': 4.0,
    }

    def __init__(self):
        self.user_item_matrix = None
        self.item_similarity_matrix = None
        self.product_features = None

    def build_user_item_matrix(self, interactions_df):
        """Xây dựng User-Item interaction matrix"""
        if interactions_df.empty:
            return None

        # Tính weighted score cho mỗi interaction
        interactions_df['weighted_score'] = interactions_df['interaction_type'].map(
            self.INTERACTION_WEIGHTS
        ) * interactions_df['score']

        # Aggregate scores per user-item pair
        user_item = interactions_df.groupby(['user_id', 'product_id'])['weighted_score'].sum().reset_index()

        # Create pivot table
        matrix = user_item.pivot(index='user_id', columns='product_id', values='weighted_score').fillna(0)

        return matrix

    def compute_item_similarity(self, user_item_matrix):
        """Tính Item-Item similarity matrix sử dụng Cosine Similarity"""
        if user_item_matrix is None or user_item_matrix.empty:
            return None

        # Transpose để có items làm rows
        item_matrix = user_item_matrix.T

        # Compute cosine similarity
        similarity = cosine_similarity(item_matrix)

        # Convert to DataFrame
        similarity_df = pd.DataFrame(
            similarity,
            index=item_matrix.index,
            columns=item_matrix.index
        )

        return similarity_df

    def get_similar_products(self, product_id, n=10):
        """Lấy n sản phẩm tương tự với product_id"""
        cache_key = f'similar_products:{product_id}:{n}'
        cached = cache.get(cache_key)
        if cached:
            return cached

        from .models import ProductSimilarity

        # Lấy từ pre-computed similarities
        similarities = ProductSimilarity.objects.filter(
            product_id=product_id
        ).order_by('-similarity_score')[:n]

        result = [
            {
                'product_id': str(sim.similar_product_id),
                'similarity_score': sim.similarity_score
            }
            for sim in similarities
        ]

        cache.set(cache_key, result, timeout=3600)
        return result

    def get_user_recommendations(self, user_id, n=10):
        """Lấy personalized recommendations cho user"""
        cache_key = f'user_recommendations:{user_id}:{n}'
        cached = cache.get(cache_key)
        if cached:
            return cached

        from .models import UserInteraction, UserRecommendation

        # Lấy từ pre-computed recommendations
        recommendations = UserRecommendation.objects.filter(
            user_id=user_id
        ).order_by('-score')[:n]

        if recommendations.exists():
            result = [
                {
                    'product_id': str(rec.product_id),
                    'score': rec.score,
                    'reason': rec.reason
                }
                for rec in recommendations
            ]
        else:
            # Fallback: Dựa trên lịch sử tương tác
            result = self._compute_realtime_recommendations(user_id, n)

        cache.set(cache_key, result, timeout=1800)
        return result

    def _compute_realtime_recommendations(self, user_id, n=10):
        """Tính recommendations realtime cho user mới"""
        from .models import UserInteraction

        # Lấy sản phẩm user đã tương tác
        user_interactions = UserInteraction.objects.filter(
            user_id=user_id
        ).values('product_id', 'interaction_type', 'score')

        if not user_interactions:
            return self.get_trending_products(n)

        recommendations = []
        seen_products = set()

        for interaction in user_interactions:
            seen_products.add(str(interaction['product_id']))
            similar = self.get_similar_products(interaction['product_id'], n=5)

            weight = self.INTERACTION_WEIGHTS.get(interaction['interaction_type'], 1.0)
            for sim in similar:
                if sim['product_id'] not in seen_products:
                    recommendations.append({
                        'product_id': sim['product_id'],
                        'score': sim['similarity_score'] * weight,
                        'reason': f"Vì bạn đã xem sản phẩm tương tự"
                    })

        # Aggregate và sort
        product_scores = {}
        for rec in recommendations:
            pid = rec['product_id']
            if pid in product_scores:
                product_scores[pid]['score'] += rec['score']
            else:
                product_scores[pid] = rec

        result = sorted(product_scores.values(), key=lambda x: x['score'], reverse=True)[:n]
        return result

    def get_trending_products(self, n=10, days=7):
        """Lấy sản phẩm trending dựa trên interactions gần đây"""
        cache_key = f'trending_products:{n}:{days}'
        cached = cache.get(cache_key)
        if cached:
            return cached

        from .models import UserInteraction
        from django.utils import timezone
        from datetime import timedelta

        since = timezone.now() - timedelta(days=days)

        # Aggregate interactions
        trending = UserInteraction.objects.filter(
            created_at__gte=since
        ).values('product_id').annotate(
            total_score=models.Sum(
                models.Case(
                    *[models.When(interaction_type=k, then=v) for k, v in self.INTERACTION_WEIGHTS.items()],
                    default=1.0,
                    output_field=models.FloatField()
                )
            )
        ).order_by('-total_score')[:n]

        result = [
            {
                'product_id': str(item['product_id']),
                'score': item['total_score'],
                'reason': 'Đang thịnh hành'
            }
            for item in trending
        ]

        cache.set(cache_key, result, timeout=1800)
        return result

    def get_frequently_bought_together(self, product_id, n=5):
        """Lấy sản phẩm thường được mua cùng"""
        cache_key = f'bought_together:{product_id}:{n}'
        cached = cache.get(cache_key)
        if cached:
            return cached

        from .models import UserInteraction

        # Tìm users đã mua product này
        buyers = UserInteraction.objects.filter(
            product_id=product_id,
            interaction_type='purchase'
        ).values_list('user_id', flat=True)

        if not buyers:
            return []

        # Tìm các sản phẩm khác mà những users này cũng mua
        other_products = UserInteraction.objects.filter(
            user_id__in=buyers,
            interaction_type='purchase'
        ).exclude(
            product_id=product_id
        ).values('product_id').annotate(
            count=models.Count('id')
        ).order_by('-count')[:n]

        result = [
            {
                'product_id': str(item['product_id']),
                'co_purchase_count': item['count'],
                'reason': 'Thường được mua cùng'
            }
            for item in other_products
        ]

        cache.set(cache_key, result, timeout=3600)
        return result

    def record_interaction(self, user_id, product_id, interaction_type, score=1.0):
        """Ghi nhận tương tác của user"""
        from .models import UserInteraction

        UserInteraction.objects.create(
            user_id=user_id,
            product_id=product_id,
            interaction_type=interaction_type,
            score=score
        )

        # Invalidate cache
        cache.delete(f'user_recommendations:{user_id}:*')

    def train_model(self):
        """Train và lưu similarity matrix"""
        from .models import UserInteraction, ProductSimilarity

        logger.info("Starting model training...")

        # Load interactions
        interactions = UserInteraction.objects.all().values(
            'user_id', 'product_id', 'interaction_type', 'score'
        )
        df = pd.DataFrame(list(interactions))

        if df.empty:
            logger.warning("No interactions data for training")
            return {'status': 'no_data'}

        # Build matrices
        user_item_matrix = self.build_user_item_matrix(df)
        if user_item_matrix is None:
            return {'status': 'failed'}

        similarity_matrix = self.compute_item_similarity(user_item_matrix)
        if similarity_matrix is None:
            return {'status': 'failed'}

        # Save to database
        ProductSimilarity.objects.all().delete()

        batch = []
        for product_id in similarity_matrix.index:
            similarities = similarity_matrix[product_id].sort_values(ascending=False)[1:11]
            for similar_id, score in similarities.items():
                if score > 0.1:  # Threshold
                    batch.append(ProductSimilarity(
                        product_id=product_id,
                        similar_product_id=similar_id,
                        similarity_score=score
                    ))

        ProductSimilarity.objects.bulk_create(batch, batch_size=1000)

        logger.info(f"Model training completed. {len(batch)} similarities saved.")
        return {
            'status': 'success',
            'products_count': len(similarity_matrix),
            'similarities_count': len(batch)
        }


# Singleton instance
recommendation_engine = RecommendationEngine()
