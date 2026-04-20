from rest_framework import serializers
from .models import Notification, NotificationTemplate

class NotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'user_id', 'type', 'type_display', 'channel', 'channel_display',
                  'title', 'message', 'data', 'is_read', 'read_at', 'created_at']
        read_only_fields = ['id', 'created_at']

class SendNotificationSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    type = serializers.ChoiceField(choices=Notification.TYPE_CHOICES)
    channel = serializers.ChoiceField(choices=Notification.CHANNEL_CHOICES, default='in_app')
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    data = serializers.JSONField(required=False, default=dict)
