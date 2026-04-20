from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from product_app.views import (
    HealthCheckView,
    CategoryListView,
    CategoryDetailView,
    ProductListCreateView,
    ProductDetailView,
    ProductSearchView,
    ProductByCategoryView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<uuid:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('', ProductListCreateView.as_view(), name='product-list'),
    path('<uuid:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('search/', ProductSearchView.as_view(), name='product-search'),
    path('category/<uuid:category_id>/', ProductByCategoryView.as_view(), name='products-by-category'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
