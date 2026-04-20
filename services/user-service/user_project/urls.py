from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from user_app.views import (
    HealthCheckView,
    ProfileView,
    AddressListCreateView,
    AddressDetailView,
    WishlistView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('addresses/', AddressListCreateView.as_view(), name='address-list'),
    path('addresses/<uuid:pk>/', AddressDetailView.as_view(), name='address-detail'),
    path('wishlist/', WishlistView.as_view(), name='wishlist'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
