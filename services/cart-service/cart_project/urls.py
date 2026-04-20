from django.contrib import admin
from django.urls import path
from cart_app.views import HealthCheckView, CartView, CartItemView, CartClearView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('', CartView.as_view(), name='cart'),
    path('items/', CartItemView.as_view(), name='cart-items'),
    path('items/<uuid:pk>/', CartItemView.as_view(), name='cart-item-detail'),
    path('clear/', CartClearView.as_view(), name='cart-clear'),
]
