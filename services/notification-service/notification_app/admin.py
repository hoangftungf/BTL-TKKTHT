from django.contrib import admin
from .models import Notification, NotificationTemplate

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user_id', 'type', 'channel', 'is_read', 'created_at')
    list_filter = ('type', 'channel', 'is_read')
    search_fields = ('title', 'message', 'user_id')

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('code', 'type', 'is_active', 'created_at')
    list_filter = ('type', 'is_active')
    search_fields = ('code', 'title_template')
