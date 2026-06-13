from django.contrib import admin
from django.urls import path
from search_app.views import (
    HealthCheckView, MetricsView, SmartSearchView, AutocompleteView,
    IndexProductsView, HybridSearchView, SmartSearchV2View,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', HealthCheckView.as_view()),
    path('metrics/', MetricsView.as_view()),
    path('', SmartSearchView.as_view()),
    path('hybrid/', HybridSearchView.as_view()),
    path('v2/', SmartSearchV2View.as_view()),
    path('autocomplete/', AutocompleteView.as_view()),
    path('index/', IndexProductsView.as_view()),
]
