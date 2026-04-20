from django.contrib import admin
from .models import Shipment, TrackingEvent

class TrackingEventInline(admin.TabularInline):
    model = TrackingEvent
    extra = 0

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'order_id', 'carrier', 'status', 'created_at')
    list_filter = ('status', 'carrier')
    search_fields = ('tracking_number', 'order_id')
    inlines = [TrackingEventInline]
