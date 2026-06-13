from django.contrib import admin
from django.urls import path
from order_app.views import (
    HealthCheckView,
    OrderListCreateView,
    OrderDetailView,
    OrderCancelView,
    OrderTrackView,
    OrderStatusUpdateView,
    OrderConfirmReceivedView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('', OrderListCreateView.as_view(), name='order-list-create'),
    path('<uuid:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('<uuid:pk>/cancel/', OrderCancelView.as_view(), name='order-cancel'),
    path('<uuid:pk>/track/', OrderTrackView.as_view(), name='order-track'),
    path('<uuid:pk>/status/', OrderStatusUpdateView.as_view(), name='order-status-update'),
    path('<uuid:pk>/confirm-received/', OrderConfirmReceivedView.as_view(), name='order-confirm-received'),
]
