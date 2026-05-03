import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from django.db.models import Q
from .models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
)

logger = logging.getLogger(__name__)


def track_behavior(user_id, action, product_id=None, category_id=None, metadata=None):
    """Send tracking request to recommendation service (async)."""
    import httpx
    import os
    from threading import Thread

    if not user_id:
        return

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
            httpx.post(f"{url}/track/", json=payload, timeout=5.0)
        except Exception as e:
            logger.warning(f"Tracking error: {e}")

    thread = Thread(target=_send)
    thread.daemon = True
    thread.start()


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'healthy', 'service': 'product-service'})


class CategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        categories = Category.objects.filter(parent__isnull=True, is_active=True)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


class CategoryDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            category = Category.objects.get(pk=pk, is_active=True)
            serializer = CategorySerializer(category)
            return Response(serializer.data)
        except Category.DoesNotExist:
            return Response({'error': 'Danh mục không tồn tại'}, status=status.HTTP_404_NOT_FOUND)


class ProductListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        queryset = Product.objects.filter(status='active').select_related('category').prefetch_related('images')

        category = request.query_params.get('category')
        if category:
            # Include products from parent category and all its children
            try:
                cat_obj = Category.objects.get(pk=category)
                child_ids = cat_obj.children.values_list('id', flat=True)
                category_ids = [cat_obj.id] + list(child_ids)
                queryset = queryset.filter(category_id__in=category_ids)
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
        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })

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
        product = self.get_object(pk)
        if not product:
            return Response({'error': 'Sản phẩm không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

        product.view_count += 1
        product.save(update_fields=['view_count'])

        # Track view_product behavior
        if request.user and request.user.is_authenticated:
            track_behavior(
                user_id=request.user.id,
                action='view_product',
                product_id=pk,
                category_id=product.category_id,
                metadata={'product_name': product.name}
            )

        serializer = ProductDetailSerializer(product)
        return Response(serializer.data)

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

        products = Product.objects.filter(
            status='active'
        ).filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query) |
            Q(sku__icontains=query)
        ).select_related('category').prefetch_related('images')[:50]

        serializer = ProductListSerializer(products, many=True)
        return Response({
            'query': query,
            'count': len(serializer.data),
            'results': serializer.data
        })


class ProductByCategoryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, category_id):
        # Include products from category and all its children
        category_name = None
        try:
            cat_obj = Category.objects.get(pk=category_id)
            category_name = cat_obj.name
            child_ids = cat_obj.children.values_list('id', flat=True)
            category_ids = [cat_obj.id] + list(child_ids)
        except Category.DoesNotExist:
            category_ids = [category_id]

        # Track view_category behavior
        if request.user and request.user.is_authenticated:
            track_behavior(
                user_id=request.user.id,
                action='view_category',
                category_id=category_id,
                metadata={'category_name': category_name}
            )

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
        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


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
