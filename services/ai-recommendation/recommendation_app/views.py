from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .engine import recommendation_engine
from .models import UserInteraction
import httpx
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'ai-recommendation',
            'models': ['collaborative', 'lstm', 'graph', 'rag', 'hybrid']
        })


class SimilarProductsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, product_id):
        """Lấy sản phẩm tương tự"""
        n = int(request.query_params.get('limit', 10))

        similar = recommendation_engine.get_similar_products(product_id, n=n)

        # Ghi nhận view interaction nếu user đã đăng nhập
        if request.user and request.user.is_authenticated:
            recommendation_engine.record_interaction(
                user_id=request.user.id,
                product_id=product_id,
                interaction_type='view'
            )

        # Fetch product details
        products = self._fetch_product_details([s['product_id'] for s in similar])

        return Response({
            'product_id': str(product_id),
            'similar_products': [
                {**s, 'product': products.get(s['product_id'])}
                for s in similar
            ]
        })

    def _fetch_product_details(self, product_ids):
        """Fetch product details từ Product Service"""
        products = {}
        for pid in product_ids:
            try:
                response = httpx.get(
                    f"{settings.PRODUCT_SERVICE_URL}/{pid}/",
                    timeout=5.0
                )
                if response.status_code == 200:
                    products[pid] = response.json()
            except Exception:
                pass
        return products


class PersonalizedRecommendationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Lấy gợi ý cá nhân hóa cho user"""
        n = int(request.query_params.get('limit', 10))

        recommendations = recommendation_engine.get_user_recommendations(
            user_id=request.user.id,
            n=n
        )

        # Fetch product details
        products = {}
        for rec in recommendations:
            try:
                response = httpx.get(
                    f"{settings.PRODUCT_SERVICE_URL}/{rec['product_id']}/",
                    timeout=5.0
                )
                if response.status_code == 200:
                    products[rec['product_id']] = response.json()
            except Exception:
                pass

        return Response({
            'user_id': str(request.user.id),
            'recommendations': [
                {**rec, 'product': products.get(rec['product_id'])}
                for rec in recommendations
            ]
        })


class TrendingProductsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Lấy sản phẩm trending"""
        n = int(request.query_params.get('limit', 10))
        days = int(request.query_params.get('days', 7))

        trending = recommendation_engine.get_trending_products(n=n, days=days)

        # Fetch product details
        products = {}
        for item in trending:
            try:
                response = httpx.get(
                    f"{settings.PRODUCT_SERVICE_URL}/{item['product_id']}/",
                    timeout=5.0
                )
                if response.status_code == 200:
                    products[item['product_id']] = response.json()
            except Exception:
                pass

        return Response({
            'period_days': days,
            'trending': [
                {**item, 'product': products.get(item['product_id'])}
                for item in trending
            ]
        })


class FrequentlyBoughtTogetherView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, product_id):
        """Lấy sản phẩm thường được mua cùng"""
        n = int(request.query_params.get('limit', 5))

        bought_together = recommendation_engine.get_frequently_bought_together(
            product_id=product_id,
            n=n
        )

        # Fetch product details
        products = {}
        for item in bought_together:
            try:
                response = httpx.get(
                    f"{settings.PRODUCT_SERVICE_URL}/{item['product_id']}/",
                    timeout=5.0
                )
                if response.status_code == 200:
                    products[item['product_id']] = response.json()
            except Exception:
                pass

        return Response({
            'product_id': str(product_id),
            'frequently_bought_together': [
                {**item, 'product': products.get(item['product_id'])}
                for item in bought_together
            ]
        })


class TrainModelView(APIView):
    permission_classes = [AllowAny]  # Should be admin only in production

    def post(self, request):
        """Trigger model training"""
        result = recommendation_engine.train_model()
        return Response(result)


class RecordInteractionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Ghi nhận user interaction"""
        product_id = request.data.get('product_id')
        interaction_type = request.data.get('type', 'view')
        score = float(request.data.get('score', 1.0))

        if not product_id:
            return Response(
                {'error': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if interaction_type not in ['view', 'cart', 'purchase', 'wishlist', 'review']:
            return Response(
                {'error': 'Invalid interaction type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        recommendation_engine.record_interaction(
            user_id=request.user.id,
            product_id=product_id,
            interaction_type=interaction_type,
            score=score
        )

        # Also record to Knowledge Graph
        try:
            from .knowledge_graph import knowledge_graph
            knowledge_graph.record_interaction(
                user_id=request.user.id,
                product_id=product_id,
                interaction_type=interaction_type
            )
        except Exception as e:
            logger.warning(f"Failed to record to graph: {e}")

        return Response({'status': 'recorded'})


# ===================== HYBRID ENGINE VIEWS =====================

class HybridRecommendationsView(APIView):
    """Hybrid recommendations combining LSTM + Graph + RAG"""
    permission_classes = [AllowAny]

    def get(self, request):
        from .hybrid_engine import hybrid_engine

        user_id = request.query_params.get('user_id')
        if request.user and request.user.is_authenticated:
            user_id = str(request.user.id)

        query = request.query_params.get('query')
        product_id = request.query_params.get('product_id')
        n = int(request.query_params.get('limit', 10))

        result = hybrid_engine.get_recommendations(
            user_id=user_id,
            query=query,
            product_id=product_id,
            n=n
        )

        # Fetch product details
        products = self._fetch_products([r['product_id'] for r in result.get('recommendations', [])])
        for rec in result.get('recommendations', []):
            rec['product'] = products.get(rec['product_id'])

        return Response(result)

    def _fetch_products(self, product_ids):
        products = {}
        for pid in product_ids:
            try:
                response = httpx.get(f"{settings.PRODUCT_SERVICE_URL}/api/products/{pid}/", timeout=5.0)
                if response.status_code == 200:
                    products[pid] = response.json()
            except Exception:
                pass
        return products


class HybridChatbotView(APIView):
    """Chatbot powered by RAG + Hybrid recommendations"""
    permission_classes = [AllowAny]

    def post(self, request):
        from .hybrid_engine import hybrid_engine

        query = request.data.get('query', '')
        user_id = request.data.get('user_id')
        if request.user and request.user.is_authenticated:
            user_id = str(request.user.id)

        if not query:
            return Response({'error': 'query is required'}, status=status.HTTP_400_BAD_REQUEST)

        result = hybrid_engine.get_chatbot_response(query=query, user_id=user_id)
        return Response(result)


# ===================== LSTM ENGINE VIEWS =====================

class LSTMPredictionsView(APIView):
    """LSTM-based sequence predictions"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .lstm_model import lstm_engine

        n = int(request.query_params.get('limit', 10))
        predictions = lstm_engine.predict(user_id=request.user.id, n=n)

        return Response({
            'user_id': str(request.user.id),
            'model': 'lstm',
            'predictions': predictions
        })


class LSTMTrainView(APIView):
    """Train LSTM model"""
    permission_classes = [AllowAny]

    def post(self, request):
        from .lstm_model import lstm_engine

        epochs = int(request.data.get('epochs', 50))
        batch_size = int(request.data.get('batch_size', 64))

        result = lstm_engine.train(epochs=epochs, batch_size=batch_size)
        return Response(result)


# ===================== KNOWLEDGE GRAPH VIEWS =====================

class GraphRecommendationsView(APIView):
    """Knowledge Graph-based recommendations"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .knowledge_graph import knowledge_graph

        n = int(request.query_params.get('limit', 10))
        recommendations = knowledge_graph.get_user_recommendations(
            user_id=request.user.id,
            n=n
        )

        return Response({
            'user_id': str(request.user.id),
            'model': 'knowledge_graph',
            'recommendations': recommendations
        })


class GraphSimilarView(APIView):
    """Get similar products from Knowledge Graph"""
    permission_classes = [AllowAny]

    def get(self, request, product_id):
        from .knowledge_graph import knowledge_graph

        n = int(request.query_params.get('limit', 10))
        similar = knowledge_graph.get_similar_products(product_id, n=n)
        bought_together = knowledge_graph.get_frequently_bought_together(product_id, n=5)

        return Response({
            'product_id': str(product_id),
            'model': 'knowledge_graph',
            'similar_products': similar,
            'frequently_bought_together': bought_together
        })


class GraphSyncView(APIView):
    """Sync data to Knowledge Graph"""
    permission_classes = [AllowAny]

    def post(self, request):
        from .knowledge_graph import knowledge_graph

        # Create indexes first
        knowledge_graph.create_indexes()

        # Sync data
        result = knowledge_graph.sync_from_database()
        return Response(result)


class GraphStatsView(APIView):
    """Get Knowledge Graph statistics"""
    permission_classes = [AllowAny]

    def get(self, request):
        from .knowledge_graph import knowledge_graph
        stats = knowledge_graph.get_stats()
        return Response(stats)


# ===================== RAG ENGINE VIEWS =====================

class RAGSearchView(APIView):
    """RAG-based semantic search"""
    permission_classes = [AllowAny]

    def get(self, request):
        from .rag_engine import rag_engine

        query = request.query_params.get('query', '')
        n = int(request.query_params.get('limit', 10))

        if not query:
            return Response({'error': 'query is required'}, status=status.HTTP_400_BAD_REQUEST)

        results = rag_engine.retrieve(query, k=n)

        return Response({
            'query': query,
            'model': 'rag',
            'results': results
        })

    def post(self, request):
        """RAG search with response generation"""
        from .rag_engine import rag_engine

        query = request.data.get('query', '')
        n = int(request.data.get('limit', 5))

        if not query:
            return Response({'error': 'query is required'}, status=status.HTTP_400_BAD_REQUEST)

        result = rag_engine.recommend(query, n=n)
        return Response(result)


class RAGIndexView(APIView):
    """Index products for RAG"""
    permission_classes = [AllowAny]

    def post(self, request):
        from .rag_engine import rag_engine
        result = rag_engine.index_products()
        return Response(result)


# ===================== TRAIN ALL MODELS =====================

class TrainAllModelsView(APIView):
    """Train all AI models"""
    permission_classes = [AllowAny]

    def post(self, request):
        from .hybrid_engine import hybrid_engine
        result = hybrid_engine.train_all_models()
        return Response(result)


# ===================== SEED DATA VIEW =====================

class SeedDataView(APIView):
    """Seed sample data for testing"""
    permission_classes = [AllowAny]

    def post(self, request):
        """Create sample data with 10 users and interactions"""
        import uuid
        import random
        from datetime import timedelta
        from django.utils import timezone
        from .models import UserInteraction, ProductSimilarity

        # Sample Users
        USERS = [
            {'id': uuid.UUID('11111111-1111-1111-1111-111111111111'), 'name': 'Nguyen Van A', 'type': 'tech_lover'},
            {'id': uuid.UUID('22222222-2222-2222-2222-222222222222'), 'name': 'Tran Thi B', 'type': 'fashionista'},
            {'id': uuid.UUID('33333333-3333-3333-3333-333333333333'), 'name': 'Le Van C', 'type': 'gamer'},
            {'id': uuid.UUID('44444444-4444-4444-4444-444444444444'), 'name': 'Pham Thi D', 'type': 'home_maker'},
            {'id': uuid.UUID('55555555-5555-5555-5555-555555555555'), 'name': 'Hoang Van E', 'type': 'sports_fan'},
            {'id': uuid.UUID('66666666-6666-6666-6666-666666666666'), 'name': 'Nguyen Thi F', 'type': 'bookworm'},
            {'id': uuid.UUID('77777777-7777-7777-7777-777777777777'), 'name': 'Tran Van G', 'type': 'tech_lover'},
            {'id': uuid.UUID('88888888-8888-8888-8888-888888888888'), 'name': 'Le Thi H', 'type': 'fashionista'},
            {'id': uuid.UUID('99999999-9999-9999-9999-999999999999'), 'name': 'Pham Van I', 'type': 'gamer'},
            {'id': uuid.UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'), 'name': 'Hoang Thi K', 'type': 'home_maker'},
        ]

        # Products by category
        PRODUCTS = {
            'electronics': [
                uuid.UUID('e1111111-1111-1111-1111-111111111111'),
                uuid.UUID('e2222222-2222-2222-2222-222222222222'),
                uuid.UUID('e3333333-3333-3333-3333-333333333333'),
                uuid.UUID('e4444444-4444-4444-4444-444444444444'),
                uuid.UUID('e5555555-5555-5555-5555-555555555555'),
                uuid.UUID('e6666666-6666-6666-6666-666666666666'),
                uuid.UUID('e7777777-7777-7777-7777-777777777777'),
                uuid.UUID('e8888888-8888-8888-8888-888888888888'),
            ],
            'gaming': [
                uuid.UUID('g1111111-1111-1111-1111-111111111111'),
                uuid.UUID('g2222222-2222-2222-2222-222222222222'),
                uuid.UUID('g3333333-3333-3333-3333-333333333333'),
                uuid.UUID('g4444444-4444-4444-4444-444444444444'),
                uuid.UUID('g5555555-5555-5555-5555-555555555555'),
                uuid.UUID('g6666666-6666-6666-6666-666666666666'),
                uuid.UUID('g7777777-7777-7777-7777-777777777777'),
            ],
            'fashion': [
                uuid.UUID('f1111111-1111-1111-1111-111111111111'),
                uuid.UUID('f2222222-2222-2222-2222-222222222222'),
                uuid.UUID('f3333333-3333-3333-3333-333333333333'),
                uuid.UUID('f4444444-4444-4444-4444-444444444444'),
                uuid.UUID('f5555555-5555-5555-5555-555555555555'),
                uuid.UUID('f6666666-6666-6666-6666-666666666666'),
                uuid.UUID('f7777777-7777-7777-7777-777777777777'),
                uuid.UUID('f8888888-8888-8888-8888-888888888888'),
            ],
            'home': [
                uuid.UUID('h1111111-1111-1111-1111-111111111111'),
                uuid.UUID('h2222222-2222-2222-2222-222222222222'),
                uuid.UUID('h3333333-3333-3333-3333-333333333333'),
                uuid.UUID('h4444444-4444-4444-4444-444444444444'),
                uuid.UUID('h5555555-5555-5555-5555-555555555555'),
                uuid.UUID('h6666666-6666-6666-6666-666666666666'),
            ],
            'sports': [
                uuid.UUID('s1111111-1111-1111-1111-111111111111'),
                uuid.UUID('s2222222-2222-2222-2222-222222222222'),
                uuid.UUID('s3333333-3333-3333-3333-333333333333'),
                uuid.UUID('s4444444-4444-4444-4444-444444444444'),
                uuid.UUID('s5555555-5555-5555-5555-555555555555'),
                uuid.UUID('s6666666-6666-6666-6666-666666666666'),
            ],
            'books': [
                uuid.UUID('b1111111-1111-1111-1111-111111111111'),
                uuid.UUID('b2222222-2222-2222-2222-222222222222'),
                uuid.UUID('b3333333-3333-3333-3333-333333333333'),
                uuid.UUID('b4444444-4444-4444-4444-444444444444'),
                uuid.UUID('b5555555-5555-5555-5555-555555555555'),
            ],
        }

        USER_PREFERENCES = {
            'tech_lover': ['electronics', 'gaming'],
            'fashionista': ['fashion'],
            'gamer': ['gaming', 'electronics'],
            'home_maker': ['home', 'electronics'],
            'sports_fan': ['sports', 'fashion'],
            'bookworm': ['books', 'home'],
        }

        # Clear existing data if requested
        if request.data.get('clear', True):
            UserInteraction.objects.all().delete()
            ProductSimilarity.objects.all().delete()

        # Get all products flat
        all_products = []
        product_categories = {}
        for category, product_ids in PRODUCTS.items():
            for pid in product_ids:
                all_products.append({'id': pid, 'category': category})
                product_categories[pid] = category

        # Generate interactions
        now = timezone.now()
        interactions_created = 0

        for user in USERS:
            preferred_cats = USER_PREFERENCES.get(user['type'], ['electronics'])
            preferred = [p for p in all_products if p['category'] in preferred_cats]
            others = [p for p in all_products if p['category'] not in preferred_cats]

            num_interactions = random.randint(15, 30)

            for i in range(num_interactions):
                product = random.choice(preferred) if random.random() < 0.8 and preferred else random.choice(others or all_products)

                progress = i / num_interactions
                rand = random.random()

                if progress < 0.3:
                    interaction_type = 'view' if rand < 0.7 else ('cart' if rand < 0.9 else 'wishlist')
                elif progress < 0.7:
                    if rand < 0.4:
                        interaction_type = 'view'
                    elif rand < 0.7:
                        interaction_type = 'cart'
                    elif rand < 0.85:
                        interaction_type = 'wishlist'
                    else:
                        interaction_type = 'purchase'
                else:
                    if rand < 0.2:
                        interaction_type = 'view'
                    elif rand < 0.4:
                        interaction_type = 'cart'
                    elif rand < 0.7:
                        interaction_type = 'purchase'
                    else:
                        interaction_type = 'review'

                timestamp = now - timedelta(
                    days=random.randint(0, 30),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )

                UserInteraction.objects.create(
                    user_id=user['id'],
                    product_id=product['id'],
                    interaction_type=interaction_type,
                    score=random.uniform(0.5, 1.0) if interaction_type != 'view' else 1.0,
                    created_at=timestamp
                )
                interactions_created += 1

        # Generate product similarities
        similarities_created = 0
        for category, product_ids in PRODUCTS.items():
            for i, p1 in enumerate(product_ids):
                for j, p2 in enumerate(product_ids):
                    if i != j:
                        ProductSimilarity.objects.create(
                            product_id=p1,
                            similar_product_id=p2,
                            similarity_score=random.uniform(0.6, 0.95)
                        )
                        similarities_created += 1

        return Response({
            'status': 'success',
            'users_count': len(USERS),
            'products_count': len(all_products),
            'interactions_created': interactions_created,
            'similarities_created': similarities_created,
            'users': [
                {'id': str(u['id']), 'name': u['name'], 'type': u['type']}
                for u in USERS
            ]
        })
