import logging
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from django.db.models import Q, F
from django.core.cache import cache
from .models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductSuggestSerializer,
)

logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=10)


def track_behavior(user_id, action, product_id=None, category_id=None, metadata=None):
    """Send tracking request to recommendation service (async via thread pool)."""
    import httpx
    import os
    from product_app.middleware.trace import get_current_trace_id

    if not user_id:
        return

    # Capture trace_id on the request thread — thread-local won't be available
    # inside the daemon thread because it runs on a different OS thread.
    trace_id = get_current_trace_id()

    def _send():
        try:
            url = os.environ.get('RECOMMENDATION_SERVICE_URL', 'http://ai-recommendation:8000')
            payload = {
                'user_id': str(user_id),
                'action': action,
                'product_id': str(product_id) if product_id else None,
                'category_id': str(category_id) if category_id else None,
                'metadata': metadata or {},
            }
            httpx.post(f"{url}/track/", json=payload, headers={'X-Trace-Id': trace_id}, timeout=5.0)
        except Exception as e:
            logger.warning(f"Tracking error: {e}")

    executor.submit(_send)


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'healthy', 'service': 'product-service'})


class CategoryListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        cache_key = "category_list"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        categories = Category.objects.filter(parent__isnull=True, is_active=True)
        serializer = CategorySerializer(categories, many=True)
        data = serializer.data
        cache.set(cache_key, data, timeout=900)  # Cache for 15 minutes
        return Response(data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            cache.delete("category_list")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        try:
            category = Category.objects.get(pk=pk, is_active=True)
            serializer = CategorySerializer(category)
            return Response(serializer.data)
        except Category.DoesNotExist:
            return Response({'error': 'Danh mục không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            category = Category.objects.get(pk=pk)
            serializer = CategorySerializer(category, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                cache.delete("category_list")
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Category.DoesNotExist:
            return Response({'error': 'Danh mục không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            category = Category.objects.get(pk=pk)
            category.delete()
            cache.delete("category_list")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Category.DoesNotExist:
            return Response({'error': 'Danh mục không tồn tại'}, status=status.HTTP_404_NOT_FOUND)


class ProductListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def _get_all_descendants_optimized(self, category_id):
        """Lay tat ca danh muc con dung query duy nhat mot lan de tranh N+1"""
        all_cats = list(Category.objects.filter(is_active=True).values('id', 'parent_id'))
        parent_map = {}
        for cat in all_cats:
            p_id = cat['parent_id']
            parent_map.setdefault(p_id, []).append(cat['id'])
        
        descendants = []
        def _recurse(cat_id):
            for child_id in parent_map.get(cat_id, []):
                descendants.append(child_id)
                _recurse(child_id)
        
        _recurse(category_id)
        return descendants

    def get(self, request):
        params = sorted(request.query_params.items())
        params_hash = hashlib.md5(json.dumps(params).encode('utf-8')).hexdigest()
        cache_key = f"product_list_{params_hash}"

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        queryset = Product.objects.filter(status='active').select_related('category').prefetch_related('images')
        sub_categories = []

        category = request.query_params.get('category')
        if category:
            try:
                cat_obj = Category.objects.get(pk=category)
                descendant_ids = self._get_all_descendants_optimized(cat_obj.id)
                category_ids = [cat_obj.id] + descendant_ids
                queryset = queryset.filter(category_id__in=category_ids)
                sub_categories = list(cat_obj.children.filter(is_active=True).values('id', 'name', 'slug'))
            except Category.DoesNotExist:
                queryset = queryset.filter(category_id=category)

        brand = request.query_params.get('brand')
        if brand:
            queryset = queryset.filter(brand__iexact=brand)

        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        is_featured = request.query_params.get('is_featured')
        if is_featured:
            queryset = queryset.filter(is_featured=True)

        ordering = request.query_params.get('ordering', '-created_at')
        valid_orderings = ['price', '-price', 'name', '-name', '-sold_count', '-rating_avg', '-created_at']
        if ordering in valid_orderings:
            queryset = queryset.order_by(ordering)

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        products = queryset[start:end]

        serializer = ProductListSerializer(products, many=True)
        response_data = {
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data,
            'sub_categories': sub_categories
        }
        cache.set(cache_key, response_data, timeout=300)  # Cache for 5 minutes
        return Response(response_data)

    def post(self, request):
        serializer = ProductDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(seller_id=request.user.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        try:
            return Product.objects.select_related('category').prefetch_related('images', 'variants').get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        cache_key = f"product_detail_{pk}"
        cached_data = cache.get(cache_key)

        if cached_data is None:
            product = self.get_object(pk)
            if not product:
                return Response({'error': 'Sản phẩm không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

            serializer = ProductDetailSerializer(product)
            cached_data = serializer.data
            cache.set(cache_key, cached_data, timeout=300)  # Cache for 5 minutes

            # Track & increment view_count
            product.view_count += 1
            product.save(update_fields=['view_count'])

            if request.user and request.user.is_authenticated:
                track_behavior(
                    user_id=request.user.id,
                    action='view_product',
                    product_id=pk,
                    category_id=product.category_id,
                    metadata={'product_name': product.name}
                )
        else:
            # Cheap update view count in DB without select
            Product.objects.filter(pk=pk).update(view_count=F('view_count') + 1)

            if request.user and request.user.is_authenticated:
                track_behavior(
                    user_id=request.user.id,
                    action='view_product',
                    product_id=pk,
                    category_id=cached_data.get('category', {}).get('id') if cached_data.get('category') else None,
                    metadata={'product_name': cached_data.get('name')}
                )

        return Response(cached_data)

    def put(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({'error': 'Sản phẩm không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

        if product.seller_id and str(product.seller_id) != str(request.user.id):
            return Response({'error': 'Bạn không có quyền sửa sản phẩm này'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ProductDetailSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        product = self.get_object(pk)
        if not product:
            return Response({'error': 'Sản phẩm không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

        if product.seller_id and str(product.seller_id) != str(request.user.id):
            return Response({'error': 'Bạn không có quyền xóa sản phẩm này'}, status=status.HTTP_403_FORBIDDEN)

        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductSearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': 'Vui lòng nhập từ khóa tìm kiếm'}, status=status.HTTP_400_BAD_REQUEST)

        # Cache search queries
        query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
        cache_key = f"product_search_{query_hash}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        from django.db import connection
        if connection.vendor == 'postgresql':
            from django.contrib.postgres.search import SearchVector, SearchQuery
            vector = SearchVector('name', weight='A') + \
                     SearchVector('description', weight='B') + \
                     SearchVector('brand', weight='C') + \
                     SearchVector('sku', weight='C')
            search_query = SearchQuery(query)
            products = Product.objects.annotate(
                search=vector
            ).filter(
                search=search_query,
                status='active'
            ).select_related('category').prefetch_related('images')[:50]
        else:
            products = Product.objects.filter(
                status='active'
            ).filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(brand__icontains=query) |
                Q(sku__icontains=query)
            ).select_related('category').prefetch_related('images')[:50]

        serializer = ProductListSerializer(products, many=True)
        response_data = {
            'query': query,
            'count': len(serializer.data),
            'results': serializer.data
        }
        cache.set(cache_key, response_data, timeout=300)  # Cache for 5 minutes
        return Response(response_data)


class ProductByCategoryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, category_id):
        category_name = None
        try:
            cat_obj = Category.objects.get(pk=category_id)
            category_name = cat_obj.name
            child_ids = cat_obj.children.values_list('id', flat=True)
            category_ids = [cat_obj.id] + list(child_ids)
        except Category.DoesNotExist:
            category_ids = [category_id]

        if request.user and request.user.is_authenticated:
            track_behavior(
                user_id=request.user.id,
                action='view_category',
                category_id=category_id,
                metadata={'category_name': category_name}
            )

        params = sorted(request.query_params.items())
        params_hash = hashlib.md5(json.dumps(params).encode('utf-8')).hexdigest()
        cache_key = f"products_by_category_{category_id}_{params_hash}"

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        products = Product.objects.filter(
            category_id__in=category_ids,
            status='active'
        ).select_related('category').prefetch_related('images')

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        total = products.count()
        products = products[start:end]

        serializer = ProductListSerializer(products, many=True)
        response_data = {
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        }
        cache.set(cache_key, response_data, timeout=300)  # Cache for 5 minutes
        return Response(response_data)


class TrackClickView(APIView):
    """Track product click from product listing (click_product action)"""
    permission_classes = [AllowAny]

    def post(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({'error': 'product_id required'}, status=status.HTTP_400_BAD_REQUEST)

        if request.user and request.user.is_authenticated:
            track_behavior(
                user_id=request.user.id,
                action='click_product',
                product_id=product_id,
                metadata=request.data.get('metadata', {})
            )
            return Response({'status': 'tracked'})

        return Response({'status': 'skipped', 'reason': 'anonymous user'})


class ProductSuggestView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '')
        if not query or len(query.strip()) < 2:
            return Response([])

        clean_query = query.strip().lower()
        query_hash = hashlib.md5(clean_query.encode('utf-8')).hexdigest()
        cache_key = f"product_suggest_{query_hash}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        from django.db import connection
        if connection.vendor == 'postgresql':
            from django.contrib.postgres.search import SearchVector, SearchQuery
            vector = SearchVector('name', weight='A') + SearchVector('brand', weight='B')
            
            # Use raw prefix query for autocomplete (e.g. 'sams:*')
            # For multi-word queries in postgres tsquery, we join them with &
            words = [word for word in clean_query.split() if word]
            if words:
                words[-1] = f"{words[-1]}:*"
                raw_query = " & ".join(words)
            else:
                raw_query = f"{clean_query}:*"
            
            search_query = SearchQuery(raw_query, search_type='raw')
            products = Product.objects.annotate(
                search=vector
            ).filter(
                search=search_query,
                status='active'
            ).select_related('category').prefetch_related('images')[:6]
        else:
            products = Product.objects.filter(
                status='active'
            ).filter(
                Q(name__icontains=clean_query) |
                Q(brand__icontains=clean_query)
            ).select_related('category').prefetch_related('images')[:6]

        serializer = ProductSuggestSerializer(products, many=True, context={'request': request})
        data = serializer.data
        cache.set(cache_key, data, timeout=600)  # 10 minutes cache
        return Response(data)
