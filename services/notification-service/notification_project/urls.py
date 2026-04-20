from django.contrib import admin
from django.urls import path
from notification_app.views import HealthCheckView, NotificationListView, NotificationDetailView, MarkReadView, SendNotificationView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', HealthCheckView.as_view()),
    path('', NotificationListView.as_view()),
    path('<uuid:pk>/', NotificationDetailView.as_view()),
    path('mark-read/', MarkReadView.as_view()),
    path('send/', SendNotificationView.as_view()),
]
