"""
Product API Views
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from uuid import UUID

from ....application.services.product_service import ProductService
from ....infrastructure.repositories.product_repository_impl import DjangoProductRepository
from ..serializers.product_serializer import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateSerializer,
    ProductUpdateSerializer,
)


def get_product_service() -> ProductService:
    """Dependency Injection - tao ProductService voi repository"""
    repository = DjangoProductRepository()
    return ProductService(repository)


class ProductListView(APIView):
    """API endpoint de lay danh sach va tao san pham"""

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        service = get_product_service()

        # Parse query params
        category_id = request.query_params.get('category')
        brand = request.query_params.get('brand')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        ordering = request.query_params.get('ordering', '-created_at')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        # Featured filter
        is_featured = request.query_params.get('is_featured')
        if is_featured:
            products = service.get_featured_products(limit=page_size)
            serializer = ProductListSerializer(products, many=True)
            return Response({
                'count': len(products),
                'page': 1,
                'page_size': page_size,
                'results': serializer.data
            })

        # Normal listing
        result = service.list_products(
            category_id=UUID(category_id) if category_id else None,
            brand=brand,
            min_price=int(min_price) if min_price else None,
            max_price=int(max_price) if max_price else None,
            ordering=ordering,
            page=page,
            page_size=page_size
        )

        serializer = ProductListSerializer(result['products'], many=True)
        return Response({
            'count': result['total'],
            'page': result['page'],
            'page_size': result['page_size'],
            'results': serializer.data
        })

    def post(self, request):
        serializer = ProductCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service = get_product_service()

        try:
            seller_id = getattr(request.user, 'id', None)
            product = service.create_product(
                seller_id=seller_id,
                **serializer.validated_data
            )
            response_serializer = ProductDetailSerializer(product)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailView(APIView):
    """API endpoint de lay, cap nhat, xoa san pham"""

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        service = get_product_service()
        product = service.get_product(pk)

        if not product:
            return Response(
                {'error': 'San pham khong ton tai'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductDetailSerializer(product)
        return Response(serializer.data)

    def put(self, request, pk):
        serializer = ProductUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        service = get_product_service()

        try:
            seller_id = getattr(request.user, 'id', None)
            product = service.update_product(
                product_id=pk,
                seller_id=seller_id,
                **serializer.validated_data
            )
            response_serializer = ProductDetailSerializer(product)
            return Response(response_serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)

    def delete(self, request, pk):
        service = get_product_service()

        try:
            seller_id = getattr(request.user, 'id', None)
            service.delete_product(product_id=pk, seller_id=seller_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)


class ProductSearchView(APIView):
    """API endpoint de tim kiem san pham"""

    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '')
        if not query or len(query) < 2:
            return Response(
                {'error': 'Vui long nhap tu khoa tim kiem (it nhat 2 ky tu)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = get_product_service()
        products = service.search_products(query, limit=50)

        serializer = ProductListSerializer(products, many=True)
        return Response({
            'query': query,
            'count': len(products),
            'results': serializer.data
        })


class ProductByCategoryView(APIView):
    """API endpoint de lay san pham theo danh muc"""

    permission_classes = [AllowAny]

    def get(self, request, category_id):
        service = get_product_service()

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        result = service.get_products_by_category(
            category_id=category_id,
            page=page,
            page_size=page_size
        )

        serializer = ProductListSerializer(result['products'], many=True)
        return Response({
            'count': result['total'],
            'page': result['page'],
            'page_size': result['page_size'],
            'results': serializer.data
        })
