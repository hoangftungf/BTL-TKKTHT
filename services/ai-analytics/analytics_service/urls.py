from django.contrib import admin
from django.urls import path, include
from analytics_app.views import HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', HealthCheckView.as_view(), name='health'),
    path('api/analytics/', include('analytics_app.urls')),
]
