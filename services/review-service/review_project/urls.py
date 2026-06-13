from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from review_app.views import (
    HealthCheckView, ReviewListCreateView, ReviewDetailView, ProductReviewsView, ProductStatsView,
    ReviewReplyCreateView, AdminReviewListView, AdminReviewVisibilityView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', HealthCheckView.as_view()),
    path('', ReviewListCreateView.as_view()),
    path('<uuid:pk>/', ReviewDetailView.as_view()),
    path('product/<uuid:product_id>/', ProductReviewsView.as_view()),
    path('product/<uuid:product_id>/stats/', ProductStatsView.as_view()),
    path('replies/<uuid:review_id>/', ReviewReplyCreateView.as_view()),
    path('admin-reviews/', AdminReviewListView.as_view()),
    path('admin-reviews/<uuid:pk>/visibility/', AdminReviewVisibilityView.as_view()),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
