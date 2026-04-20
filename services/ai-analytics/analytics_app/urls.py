from django.urls import path
from .views import (
    HealthCheckView,
    DashboardView,
    SalesReportView,
    ProductAnalyticsView,
    SalesPredictionView,
    CustomerSegmentView,
    TrendAnalysisView,
)

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('sales/', SalesReportView.as_view(), name='sales-report'),
    path('products/', ProductAnalyticsView.as_view(), name='product-analytics'),
    path('predictions/', SalesPredictionView.as_view(), name='predictions'),
    path('customers/segments/', CustomerSegmentView.as_view(), name='customer-segments'),
    path('trends/', TrendAnalysisView.as_view(), name='trends'),
]
