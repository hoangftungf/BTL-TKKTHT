import uuid
from django.db import models

class Shipment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Chờ lấy hàng'),
        ('picked_up', 'Đã lấy hàng'),
        ('in_transit', 'Đang vận chuyển'),
        ('out_for_delivery', 'Đang giao hàng'),
        ('delivered', 'Đã giao'),
        ('failed', 'Giao thất bại'),
        ('returned', 'Đã hoàn trả'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.UUIDField(verbose_name='ID đơn hàng')
    tracking_number = models.CharField(max_length=50, unique=True, verbose_name='Mã vận đơn')
    carrier = models.CharField(max_length=100, default='Giao hàng nhanh', verbose_name='Đơn vị vận chuyển')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    recipient_name = models.CharField(max_length=255)
    recipient_phone = models.CharField(max_length=15)
    shipping_address = models.TextField()
    weight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    estimated_delivery = models.DateField(blank=True, null=True)
    actual_delivery = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shipments'

class TrackingEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, related_name='events')
    status = models.CharField(max_length=20)
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tracking_events'
        ordering = ['-created_at']
