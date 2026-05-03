import logging
import os
from threading import Thread
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .engine import search_engine
import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


def track_search(user_id, query, results_count=0, metadata=None):
    """Send search tracking request to recommendation service (async)."""
    if not user_id:
        return

    def _send():
        try:
            url = os.environ.get('RECOMMENDATION_SERVICE_URL', 'http://ai-recommendation:8008')
            payload = {
                'user_id': str(user_id),
                'action': 'search',
                'search_query': query,
                'metadata': {
                    'results_count': results_count,
                    **(metadata or {})
                },
            }
            httpx.post(f"{url}/track/", json=payload, timeout=5.0)
        except Exception as e:
            logger.warning(f"Tracking error: {e}")

    thread = Thread(target=_send)
    thread.daemon = True
    thread.start()


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'ai-search'
        })


class SmartSearchView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Tìm kiếm thông minh"""
        query = request.data.get('query', request.data.get('q', ''))
        page = int(request.data.get('page', 1))
        page_size = int(request.data.get('page_size', 20))

        filters = {
            'category': request.data.get('category'),
            'brand': request.data.get('brand'),
            'min_price': request.data.get('min_price'),
            'max_price': request.data.get('max_price'),
        }
        filters = {k: v for k, v in filters.items() if v}

        result = search_engine.search(
            query=query,
            filters=filters if filters else None,
            page=page,
            page_size=page_size
        )

        # Track search behavior
        if request.user and request.user.is_authenticated and query:
            track_search(
                user_id=request.user.id,
                query=query,
                results_count=result.get('count', 0),
                metadata={'filters': filters, 'page': page}
            )

        # Fetch full product details
        if result['results']:
            product_ids = [r['product_id'] for r in result['results']]
            products = self._fetch_products(product_ids)

            for r in result['results']:
                r['product'] = products.get(str(r['product_id']))

        return Response(result)

    def get(self, request):
        """GET endpoint cho tìm kiếm"""
        query = request.query_params.get('q', '')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        result = search_engine.search(
            query=query,
            page=page,
            page_size=page_size
        )

        # Track search behavior
        if request.user and request.user.is_authenticated and query:
            track_search(
                user_id=request.user.id,
                query=query,
                results_count=result.get('count', 0),
                metadata={'page': page}
            )

        return Response(result)

    def _fetch_products(self, product_ids):
        """Fetch product details"""
        products = {}
        for pid in product_ids:
            try:
                response = httpx.get(
                    f"{settings.PRODUCT_SERVICE_URL}/{pid}/",
                    timeout=5.0
                )
                if response.status_code == 200:
                    products[str(pid)] = response.json()
            except Exception:
                pass
        return products


class AutocompleteView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Gợi ý tìm kiếm"""
        query = request.query_params.get('q', '')
        limit = int(request.query_params.get('limit', 10))

        suggestions = search_engine.autocomplete(query, limit)

        return Response({
            'query': query,
            'suggestions': suggestions
        })


class IndexProductsView(APIView):
    permission_classes = [AllowAny]  # Should be admin only

    def post(self, request):
        """Index/Reindex products"""
        product = request.data.get('product')

        if product:
            # Index single product
            search_engine.index_product(product)
            return Response({'status': 'indexed', 'product_id': product.get('id')})
        else:
            # Reindex all
            result = search_engine.reindex_all()
            return Response(result)
