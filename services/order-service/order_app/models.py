import uuid
from django.db import models
from django.utils import timezone


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Chờ xác nhận'),
        ('confirmed', 'Đã xác nhận'),
        ('processing', 'Đang xử lý'),
        ('shipping', 'Đang giao hàng'),
        ('delivered', 'Đã giao hàng'),
        ('completed', 'Hoàn thành'),
        ('cancelled', 'Đã hủy'),
        ('refunded', 'Đã hoàn tiền'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Chờ thanh toán'),
        ('paid', 'Đã thanh toán'),
        ('failed', 'Thanh toán thất bại'),
        ('refunded', 'Đã hoàn tiền'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cod', 'Thanh toán khi nhận hàng'),
        ('momo', 'Ví MoMo'),
        ('vnpay', 'VNPay'),
        ('bank_transfer', 'Chuyển khoản'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=50, unique=True, verbose_name='Mã đơn hàng')
    user_id = models.UUIDField(verbose_name='ID người dùng')

    recipient_name = models.CharField(max_length=255, verbose_name='Tên người nhận')
    recipient_phone = models.CharField(max_length=15, verbose_name='SĐT người nhận')
    shipping_address = models.TextField(verbose_name='Địa chỉ giao hàng')
    shipping_province = models.CharField(max_length=100, verbose_name='Tỉnh/Thành phố')
    shipping_district = models.CharField(max_length=100, verbose_name='Quận/Huyện')
    shipping_ward = models.CharField(max_length=100, verbose_name='Phường/Xã')

    subtotal = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='Tạm tính')
    shipping_fee = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='Phí vận chuyển')
    discount_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='Giảm giá')
    total_amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='Tổng tiền')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Trạng thái')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name='Trạng thái thanh toán')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name='Phương thức thanh toán')

    note = models.TextField(blank=True, verbose_name='Ghi chú')
    cancel_reason = models.TextField(blank=True, verbose_name='Lý do hủy')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ngày cập nhật')
    confirmed_at = models.DateTimeField(blank=True, null=True, verbose_name='Ngày xác nhận')
    shipped_at = models.DateTimeField(blank=True, null=True, verbose_name='Ngày giao hàng')
    delivered_at = models.DateTimeField(blank=True, null=True, verbose_name='Ngày nhận hàng')

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD{timezone.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:4].upper()}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_id = models.UUIDField(verbose_name='ID sản phẩm')
    variant_id = models.UUIDField(blank=True, null=True, verbose_name='ID biến thể')
    product_name = models.CharField(max_length=255, verbose_name='Tên sản phẩm')
    product_image = models.URLField(blank=True, verbose_name='Hình ảnh')
    sku = models.CharField(max_length=100, verbose_name='SKU')
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='Giá')
    quantity = models.IntegerField(verbose_name='Số lượng')
    subtotal = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='Thành tiền')

    class Meta:
        db_table = 'order_items'


class OrderStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, verbose_name='Trạng thái')
    note = models.TextField(blank=True, verbose_name='Ghi chú')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời gian')
    created_by = models.UUIDField(blank=True, null=True, verbose_name='Người tạo')

    class Meta:
        db_table = 'order_status_history'
        ordering = ['-created_at']
