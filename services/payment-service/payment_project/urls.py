from django.contrib import admin
from django.urls import path
from payment_app.views import (
    HealthCheckView, MoMoPaymentView, VNPayPaymentView, CODPaymentView,
    PaymentStatusView, MoMoWebhookView, VNPayReturnView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('momo/', MoMoPaymentView.as_view(), name='momo-payment'),
    path('vnpay/', VNPayPaymentView.as_view(), name='vnpay-payment'),
    path('cod/', CODPaymentView.as_view(), name='cod-payment'),
    path('<uuid:order_id>/status/', PaymentStatusView.as_view(), name='payment-status'),
    path('webhook/momo/', MoMoWebhookView.as_view(), name='momo-webhook'),
    path('vnpay/return/', VNPayReturnView.as_view(), name='vnpay-return'),
]
