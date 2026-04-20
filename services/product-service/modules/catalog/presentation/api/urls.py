"""
Catalog API URLs
"""
from django.urls import path

from .views import (
    HealthCheckView,
    ProductListView,
    ProductDetailView,
    ProductSearchView,
    ProductByCategoryView,
    CategoryListView,
    CategoryDetailView,
)

urlpatterns = [
    # Health check
    path('health/', HealthCheckView.as_view(), name='health-check'),

    # Products
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<uuid:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/search/', ProductSearchView.as_view(), name='product-search'),
    path('products/category/<uuid:category_id>/', ProductByCategoryView.as_view(), name='product-by-category'),

    # Categories
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<uuid:pk>/', CategoryDetailView.as_view(), name='category-detail'),
]
