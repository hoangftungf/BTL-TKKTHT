from django.contrib import admin
from django.urls import path
from order_app.views import HealthCheckView, OrderListCreateView, OrderDetailView, OrderCancelView, OrderTrackView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('', OrderListCreateView.as_view(), name='order-list-create'),
    path('<uuid:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('<uuid:pk>/cancel/', OrderCancelView.as_view(), name='order-cancel'),
    path('<uuid:pk>/track/', OrderTrackView.as_view(), name='order-track'),
]
