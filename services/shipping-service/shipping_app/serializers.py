from rest_framework import serializers
from .models import Shipment, TrackingEvent

class TrackingEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingEvent
        fields = ['id', 'status', 'location', 'description', 'created_at']

class ShipmentSerializer(serializers.ModelSerializer):
    events = TrackingEventSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Shipment
        fields = '__all__'
