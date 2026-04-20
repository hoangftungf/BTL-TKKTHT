from django.contrib import admin
from django.urls import path
from shipping_app.views import HealthCheckView, ShipmentListView, ShipmentDetailView, TrackingView, ShippingRateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', HealthCheckView.as_view()),
    path('', ShipmentListView.as_view()),
    path('<uuid:pk>/', ShipmentDetailView.as_view()),
    path('track/<str:tracking_number>/', TrackingView.as_view()),
    path('rates/', ShippingRateView.as_view()),
]
