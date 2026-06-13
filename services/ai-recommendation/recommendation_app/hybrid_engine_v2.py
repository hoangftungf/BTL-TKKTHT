"""
Hybrid Recommendation Engine V2 (Phase 3)
===========================================

Replaces the old HybridEngine (LSTM + Graph + RAG) with:
1. CollaborativeFilter — online user-item cosine similarity (no pre-training)
2. KGRecommender — Neo4j graph queries via unified kg_client
3. ContentBasedRecommender — FAISS semantic search via unified vector_store
4. Multi-Armed Bandit — exploration/exploitation (epsilon-greedy)
5. Adaptive Weights — based on user history density, query specificity, feedback CTR

Removed:
- LSTM model (heavy, requires training, marginal benefit for <10K users)
- Fixed static weights (now adaptive)
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from asgiref.sync import sync_to_async
from django.core.cache import cache

logger = logging.getLogger(__name__)


# =====================================================================
# Sub-Recommenders
# =====================================================================

class CollaborativeFilter:
    """
    Online Collaborative Filtering using item-based cosine similarity.

    Computes similarity on-the-fly from UserBehavior interaction matrix.
    No pre-training required — uses Django ORM + numpy.
    """

    # Action weights for building user-item matrix
    ACTION_WEIGHTS = {
        'purchase': 5.0,
        'add_to_cart': 3.0,
        'add_to_wishlist': 2.5,
        'click_product': 1.5,
        'view_product': 1.0,
    }

    def recommend(self, user_id: str, n: int = 10) -> List[Dict]:
        """
        Get collaborative recommendations for a user.

        Strategy: find products similar to what the user has interacted with,
        based on co-occurrence patterns.
        """
        cache_key = f"collab_v2:{user_id}:{n}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            from recommendation_app.models import UserBehavior

            # Get user's recent interactions (last 90 days)
            interacted = UserBehavior.objects.filter(
                user_id=user_id,
                action__in=self.ACTION_WEIGHTS.keys(),
            ).values('product_id', 'action').distinct()[:50]

            if not interacted:
                return []

            user_product_ids = set()
            action_map = {}
            for row in interacted:
                pid = str(row['product_id'])
                if pid and pid != 'None':
                    user_product_ids.add(pid)
                    weight = self.ACTION_WEIGHTS.get(row['action'], 1.0)
                    action_map[pid] = max(action_map.get(pid, 0), weight)

            # Find co-occurring products: users who bought same items
            co_occurring = UserBehavior.objects.filter(
                product_id__in=user_product_ids,
                action__in=['purchase', 'add_to_cart'],
            ).exclude(
                user_id=user_id,
            ).values('product_id').annotate(
                co_count=Count('user_id', distinct=True),
            ).order_by('-co_count')[:n * 2]

            results = []
            for row in co_occurring:
                pid = str(row['product_id'])
                if pid not in user_product_ids:
                    results.append({
                        'product_id': pid,
                        'score': min(float(row['co_count']) / 10.0, 1.0),
                        'reason': 'Người dùng tương tự cũng thích (Collaborative)',
                    })

            results = results[:n]
            cache.set(cache_key, results, timeout=1800)  # 30 min
            return results

        except Exception as e:
            logger.error(f"CollaborativeFilter error: {e}")
            return []


class KGRecommender:
    """
    Knowledge Graph recommender using unified kg_client (Neo4j).
    """

    def recommend(self, user_id: str, n: int = 10) -> List[Dict]:
        """Get KG-based recommendations."""
        try:
            from lib.ai_core.neo4j_client import kg_client

            # Get personalized graph recommendations
            recs = kg_client.get_user_recommendations(user_id, n=n)
            for r in recs:
                r['reason'] = r.get('reason', 'Gợi ý từ Knowledge Graph')
                r['score'] = min(float(r.get('score', 0)) / 10.0, 1.0)
            return recs
        except Exception as e:
            logger.error(f"KGRecommender error: {e}")
            return []

    def similar(self, product_id: str, n: int = 10) -> List[Dict]:
        """Get similar products from KG."""
        try:
            from lib.ai_core.neo4j_client import kg_client
            return kg_client.get_similar_products(product_id, n=n)
        except Exception as e:
            logger.error(f"KGRecommender similar error: {e}")
            return []

    def trending(self, n: int = 10) -> List[Dict]:
        """Get trending products from KG."""
        try:
            from lib.ai_core.neo4j_client import kg_client
            return kg_client.get_trending(n=n)
        except Exception as e:
            logger.error(f"KGRecommender trending error: {e}")
            return []


class ContentBasedRecommender:
    """
    Content-based recommender using unified vector_store (FAISS).
    """

    def recommend(self, query: str, n: int = 10) -> List[Dict]:
        """Get content-based recommendations by semantic similarity."""
        if not query:
            return []
        try:
            from lib.ai_core.embedder import embedder
            from lib.ai_core.vector_store import vector_store

            emb = embedder.embed_sync([query])
            if len(emb) == 0:
                return []

            results = vector_store.search(emb[0], k=n)
            for r in results:
                r['reason'] = 'Phù hợp ngữ nghĩa (Content-Based)'
                r['score'] = min(float(r.get('score', 0)), 1.0)
                r['product_id'] = str(r['product_id'])
            return results
        except Exception as e:
            logger.error(f"ContentBasedRecommender error: {e}")
            return []

    def similar_by_embedding(self, product_id: str, n: int = 10) -> List[Dict]:
        """Get similar products by embedding similarity."""
        try:
            from lib.ai_core.vector_store import vector_store

            pid_str = str(product_id)
            if pid_str not in vector_store.product_data:
                return []

            product = vector_store.product_data[pid_str]
            query = f"{product.get('name', '')} {product.get('category', '')} {product.get('brand', '')}"

            results = self.recommend(query, n=n + 1)
            return [r for r in results if r['product_id'] != pid_str][:n]
        except Exception as e:
            logger.error(f"ContentBasedRecommender similar error: {e}")
            return []


# =====================================================================
# HybridEngineV2
# =====================================================================

class HybridEngineV2:
    """
    Hybrid Recommendation Engine V2.

    Aggregates recommendations from 4 sources with adaptive weights:
    1. Collaborative Filtering (online)
    2. Knowledge Graph (Neo4j)
    3. Content-Based (FAISS)
    4. Popular / Trending (fallback)

    Uses Multi-Armed Bandit for exploration and FeedbackCollector
    for adaptive weight adjustment.
    """

    def __init__(self):
        self.collab = CollaborativeFilter()
        self.kg = KGRecommender()
        self.content = ContentBasedRecommender()
        # Lazy import to avoid circular
        self._bandit = None
        self._feedback = None

    @property
    def bandit(self):
        if self._bandit is None:
            from recommendation_app.bandit import bandit
            self._bandit = bandit
        return self._bandit

    @property
    def feedback(self):
        if self._feedback is None:
            from recommendation_app.feedback import feedback_collector
            self._feedback = feedback_collector
        return self._feedback

    # ──────────────────────────────────────────────
    # Main recommend() API
    # ──────────────────────────────────────────────

    def recommend(
        self,
        user_id: Optional[str] = None,
        query: Optional[str] = None,
        product_id: Optional[str] = None,
        n: int = 10,
    ) -> Dict:
        """
        Get hybrid recommendations combining all sources.

        Args:
            user_id: user ID for personalized recommendations
            query: natural language query for content-based search
            product_id: get similar products to this product
            n: number of results

        Returns:
            dict with recommendations, weights, sources breakdown
        """
        # ── 1. Compute adaptive weights ─────────────────────────────────
        density = self._get_user_density(user_id)
        query_specificity = self._estimate_query_specificity(query)
        weights = self.feedback.compute_optimal_weights(
            density=density,
            query_specificity=query_specificity,
        )
        logger.info(
            '[HybridV2] weights=%s density=%.2f query_spec=%.2f',
            weights, density, query_specificity,
        )

        # ── 2. Gather candidates from all sources in parallel ────────────
        candidates: Dict[str, Dict] = {}

        if user_id:
            collab_recs = self.collab.recommend(user_id, n=n * 2)
            for r in collab_recs:
                self._add_candidate(candidates, r, 'collab')

            kg_recs = self.kg.recommend(user_id, n=n * 2)
            for r in kg_recs:
                self._add_candidate(candidates, r, 'kg')

        if query:
            content_recs = self.content.recommend(query, n=n * 2)
            for r in content_recs:
                self._add_candidate(candidates, r, 'content')

        if product_id:
            similar = self._get_similar_from_all(product_id, n=n)
            for r in similar:
                self._add_candidate(candidates, r, r.get('source', 'content'))

        # ── 3. Fallback: trending if no candidates ──────────────────────
        if not candidates:
            trending = self.kg.trending(n=n)
            for r in trending:
                self._add_candidate(candidates, r, 'popular')
            # Use uniform weights for fallback-only results
            weights = {'collab': 0, 'kg': 0, 'content': 0, 'popular': 1.0}

        # ── 4. Score and rank ──────────────────────────────────────────
        results = []
        for pid, data in candidates.items():
            hybrid_score = 0.0
            for source, weight in weights.items():
                hybrid_score += weight * data.get(f'{source}_score', 0)

            # Bandit exploration bonus
            if self.bandit.should_explore(user_id):
                hybrid_score += 0.05  # Small exploration boost

            reasons = list(dict.fromkeys(data.get('reasons', [])))
            results.append({
                'product_id': pid,
                'score': round(hybrid_score, 4),
                'scores_detail': {
                    s: round(data.get(f'{s}_score', 0), 4) for s in weights if weights[s] > 0
                },
                'sources': list(dict.fromkeys(data.get('sources', []))),
                'reasons': reasons[:3],
                'primary_reason': reasons[0] if reasons else 'Đề xuất cho bạn',
            })

        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:n]

        # ── 5. Record impressions for feedback loop ─────────────────────
        for pos, r in enumerate(results):
            for source in r.get('sources', ['popular']):
                self.feedback.record_impression(user_id, r['product_id'], source, pos)

        return {
            'user_id': str(user_id) if user_id else None,
            'query': query,
            'product_id': str(product_id) if product_id else None,
            'recommendations': results,
            'weights': weights,
            'total_candidates': len(candidates),
        }

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _add_candidate(self, pool: Dict, rec: Dict, source: str):
        """Add a recommendation to the candidate pool with dedup."""
        pid = str(rec.get('product_id', ''))
        if not pid:
            return

        if pid not in pool:
            pool[pid] = {
                'reasons': [],
                'sources': [],
            }

        score = min(float(rec.get('score', 0)), 1.0)

        # Normalize score if > 1 (some sources return unnormalized)
        if score > 1.0:
            score = min(score / 100.0, 1.0)

        pool[pid][f'{source}_score'] = score
        pool[pid]['sources'].append(source)

        reason = rec.get('reason', '')
        if reason:
            pool[pid]['reasons'].append(reason)

    def _get_user_density(self, user_id: Optional[str]) -> float:
        """
        Estimate user history density (0.0 = new user, 1.0 = power user).
        Based on number of interactions in the last 90 days.
        """
        if not user_id:
            return 0.0

        cache_key = f"hybridv2:density:{user_id}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            from recommendation_app.models import UserBehavior
            from datetime import timedelta
            from django.utils import timezone

            count = UserBehavior.objects.filter(
                user_id=user_id,
                created_at__gte=timezone.now() - timedelta(days=90),
            ).count()

            # Scale: 0 interactions → 0.0, 100+ interactions → 1.0
            density = min(count / 100.0, 1.0)
            cache.set(cache_key, density, timeout=3600)
            return density
        except Exception:
            return 0.0

    @staticmethod
    def _estimate_query_specificity(query: Optional[str]) -> float:
        """
        Estimate how specific a query is (0.0 = vague, 1.0 = very specific).

        Specific queries have: category + brand + price constraints.
        """
        if not query:
            return 0.0

        specificity = 0.0
        q = query.lower()

        # Category mention → 0.3
        categories = ['laptop', 'điện thoại', 'giày', 'áo', 'quần', 'tai nghe',
                      'đồng hồ', 'máy tính', 'tablet', 'túi']
        if any(c in q for c in categories):
            specificity += 0.3

        # Brand mention → +0.3
        brands = ['apple', 'samsung', 'nike', 'adidas', 'dell', 'asus', 'sony',
                  'xiaomi', 'lenovo', 'hp']
        if any(b in q for b in brands):
            specificity += 0.3

        # Price mention → +0.3
        if any(p in q for p in ['giá', 'triệu', 'tr', 'k', 'nghìn', 'đắt', 'rẻ']):
            specificity += 0.3

        # Attribute mention → +0.1
        if any(a in q for a in ['ram', 'gb', 'ssd', 'màu', 'size', 'loại']):
            specificity += 0.1

        return min(specificity, 1.0)

    def _get_similar_from_all(self, product_id: str, n: int) -> List[Dict]:
        """Get similar products from all available sources."""
        results = []
        seen = set()

        for rec in self.kg.similar(product_id, n=n):
            pid = rec.get('product_id')
            if pid and pid not in seen:
                seen.add(pid)
                rec['source'] = 'kg'
                results.append(rec)

        for rec in self.content.similar_by_embedding(product_id, n=n):
            pid = rec.get('product_id')
            if pid and pid not in seen:
                seen.add(pid)
                rec['source'] = 'content'
                results.append(rec)

        return results[:n]


# Singleton instance
hybrid_engine_v2 = HybridEngineV2()
