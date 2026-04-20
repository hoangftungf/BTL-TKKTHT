from django.contrib import admin
from django.urls import path, include
from .views import (
    HealthCheckView,
    ProxyAuthView,
    ProxyUserView,
    ProxyProductView,
    ProxyCartView,
    ProxyOrderView,
    ProxyPaymentView,
    ProxyShippingView,
    ProxyReviewView,
    ProxyNotificationView,
    ProxyRecommendationView,
    ProxySearchView,
    ProxyChatbotView,
    ProxyAnalyticsView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', HealthCheckView.as_view(), name='health-check'),

    # Proxy routes to microservices
    path('api/auth/', ProxyAuthView.as_view(), name='proxy-auth'),
    path('api/auth/<path:path>', ProxyAuthView.as_view(), name='proxy-auth-path'),

    path('api/users/', ProxyUserView.as_view(), name='proxy-user'),
    path('api/users/<path:path>', ProxyUserView.as_view(), name='proxy-user-path'),

    path('api/products/', ProxyProductView.as_view(), name='proxy-product'),
    path('api/products/<path:path>', ProxyProductView.as_view(), name='proxy-product-path'),

    path('api/cart/', ProxyCartView.as_view(), name='proxy-cart'),
    path('api/cart/<path:path>', ProxyCartView.as_view(), name='proxy-cart-path'),

    path('api/orders/', ProxyOrderView.as_view(), name='proxy-order'),
    path('api/orders/<path:path>', ProxyOrderView.as_view(), name='proxy-order-path'),

    path('api/payments/', ProxyPaymentView.as_view(), name='proxy-payment'),
    path('api/payments/<path:path>', ProxyPaymentView.as_view(), name='proxy-payment-path'),

    path('api/shipping/', ProxyShippingView.as_view(), name='proxy-shipping'),
    path('api/shipping/<path:path>', ProxyShippingView.as_view(), name='proxy-shipping-path'),

    path('api/reviews/', ProxyReviewView.as_view(), name='proxy-review'),
    path('api/reviews/<path:path>', ProxyReviewView.as_view(), name='proxy-review-path'),

    path('api/notifications/', ProxyNotificationView.as_view(), name='proxy-notification'),
    path('api/notifications/<path:path>', ProxyNotificationView.as_view(), name='proxy-notification-path'),

    # AI Services
    path('api/recommendations/', ProxyRecommendationView.as_view(), name='proxy-recommendation'),
    path('api/recommendations/<path:path>', ProxyRecommendationView.as_view(), name='proxy-recommendation-path'),

    path('api/search/', ProxySearchView.as_view(), name='proxy-search'),
    path('api/search/<path:path>', ProxySearchView.as_view(), name='proxy-search-path'),

    path('api/chatbot/', ProxyChatbotView.as_view(), name='proxy-chatbot'),
    path('api/chatbot/<path:path>', ProxyChatbotView.as_view(), name='proxy-chatbot-path'),

    path('api/analytics/', ProxyAnalyticsView.as_view(), name='proxy-analytics'),
    path('api/analytics/<path:path>', ProxyAnalyticsView.as_view(), name='proxy-analytics-path'),
]
