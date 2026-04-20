from django.contrib import admin
from django.urls import path, include
from chatbot_app.views import HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', HealthCheckView.as_view(), name='health'),
    path('api/chatbot/', include('chatbot_app.urls')),
]
