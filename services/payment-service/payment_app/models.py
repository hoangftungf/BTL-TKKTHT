import uuid
from django.db import models


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Chờ thanh toán'),
        ('processing', 'Đang xử lý'),
        ('completed', 'Thành công'),
        ('failed', 'Thất bại'),
        ('cancelled', 'Đã hủy'),
        ('refunded', 'Đã hoàn tiền'),
    ]

    METHOD_CHOICES = [
        ('momo', 'Ví MoMo'),
        ('vnpay', 'VNPay'),
        ('cod', 'Thanh toán khi nhận hàng'),
        ('bank_transfer', 'Chuyển khoản'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_id = models.UUIDField(verbose_name='ID đơn hàng')
    user_id = models.UUIDField(verbose_name='ID người dùng')
    transaction_id = models.CharField(max_length=100, unique=True, verbose_name='Mã giao dịch')

    method = models.CharField(max_length=20, choices=METHOD_CHOICES, verbose_name='Phương thức')
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='Số tiền')
    currency = models.CharField(max_length=3, default='VND', verbose_name='Tiền tệ')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Trạng thái')

    provider_transaction_id = models.CharField(max_length=100, blank=True, verbose_name='Mã GD nhà cung cấp')
    provider_response = models.JSONField(default=dict, verbose_name='Response nhà cung cấp')

    payment_url = models.URLField(blank=True, verbose_name='URL thanh toán')
    return_url = models.URLField(blank=True, verbose_name='URL trả về')

    paid_at = models.DateTimeField(blank=True, null=True, verbose_name='Thời gian thanh toán')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ngày cập nhật')

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_id} - {self.amount} {self.currency}"


class Refund(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Chờ xử lý'),
        ('processing', 'Đang xử lý'),
        ('completed', 'Hoàn thành'),
        ('failed', 'Thất bại'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    refund_id = models.CharField(max_length=100, unique=True, verbose_name='Mã hoàn tiền')
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='Số tiền')
    reason = models.TextField(verbose_name='Lý do')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Trạng thái')
    provider_response = models.JSONField(default=dict, verbose_name='Response nhà cung cấp')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name='Ngày hoàn thành')

    class Meta:
        db_table = 'refunds'
