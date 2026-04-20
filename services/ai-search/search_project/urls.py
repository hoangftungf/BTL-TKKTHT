from django.contrib import admin
from django.urls import path
from search_app.views import HealthCheckView, SmartSearchView, AutocompleteView, IndexProductsView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', HealthCheckView.as_view()),
    path('', SmartSearchView.as_view()),
    path('autocomplete/', AutocompleteView.as_view()),
    path('index/', IndexProductsView.as_view()),
]
