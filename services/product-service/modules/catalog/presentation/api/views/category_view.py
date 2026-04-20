"""
Category API Views
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from ....application.services.category_service import CategoryService
from ....infrastructure.repositories.category_repository_impl import DjangoCategoryRepository
from ..serializers.category_serializer import CategorySerializer


def get_category_service() -> CategoryService:
    """Dependency Injection - tao CategoryService voi repository"""
    repository = DjangoCategoryRepository()
    return CategoryService(repository)


class CategoryListView(APIView):
    """API endpoint de lay danh sach danh muc"""

    permission_classes = [AllowAny]

    def get(self, request):
        service = get_category_service()
        categories = service.get_category_tree()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


class CategoryDetailView(APIView):
    """API endpoint de lay chi tiet danh muc"""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        service = get_category_service()
        category = service.get_category(pk)

        if not category:
            return Response(
                {'error': 'Danh muc khong ton tai'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CategorySerializer(category)
        return Response(serializer.data)
