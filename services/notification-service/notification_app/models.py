import uuid
from django.db import models

class Notification(models.Model):
    TYPE_CHOICES = [
        ('order', 'Đơn hàng'),
        ('payment', 'Thanh toán'),
        ('shipping', 'Vận chuyển'),
        ('promotion', 'Khuyến mãi'),
        ('system', 'Hệ thống'),
    ]

    CHANNEL_CHOICES = [
        ('in_app', 'Trong ứng dụng'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push notification'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(verbose_name='ID người dùng')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='Loại')
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='in_app', verbose_name='Kênh')
    title = models.CharField(max_length=255, verbose_name='Tiêu đề')
    message = models.TextField(verbose_name='Nội dung')
    data = models.JSONField(default=dict, blank=True, verbose_name='Dữ liệu bổ sung')
    is_read = models.BooleanField(default=False, verbose_name='Đã đọc')
    read_at = models.DateTimeField(blank=True, null=True, verbose_name='Thời gian đọc')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', '-created_at']),
            models.Index(fields=['user_id', 'is_read']),
        ]

class NotificationTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=100, unique=True, verbose_name='Mã template')
    type = models.CharField(max_length=20, verbose_name='Loại')
    title_template = models.CharField(max_length=255, verbose_name='Template tiêu đề')
    message_template = models.TextField(verbose_name='Template nội dung')
    is_active = models.BooleanField(default=True, verbose_name='Hoạt động')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notification_templates'
