import uuid
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name='Tên danh mục')
    slug = models.SlugField(max_length=255, unique=True, verbose_name='Slug')
    description = models.TextField(blank=True, verbose_name='Mô tả')
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name='Hình ảnh')
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, blank=True, null=True,
        related_name='children', verbose_name='Danh mục cha'
    )
    is_active = models.BooleanField(default=True, verbose_name='Hoạt động')
    display_order = models.IntegerField(default=0, verbose_name='Thứ tự hiển thị')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ngày cập nhật')

    class Meta:
        db_table = 'categories'
        verbose_name = 'Danh mục'
        verbose_name_plural = 'Danh mục'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class Product(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Nháp'),
        ('active', 'Đang bán'),
        ('inactive', 'Ngừng bán'),
        ('out_of_stock', 'Hết hàng'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name='Tên sản phẩm')
    slug = models.SlugField(max_length=255, unique=True, verbose_name='Slug')
    description = models.TextField(blank=True, verbose_name='Mô tả')
    short_description = models.CharField(max_length=500, blank=True, verbose_name='Mô tả ngắn')
    sku = models.CharField(max_length=100, unique=True, verbose_name='Mã SKU')
    price = models.DecimalField(
        max_digits=12, decimal_places=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Giá'
    )
    compare_price = models.DecimalField(
        max_digits=12, decimal_places=0, blank=True, null=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Giá so sánh'
    )
    cost_price = models.DecimalField(
        max_digits=12, decimal_places=0, blank=True, null=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Giá vốn'
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='products', verbose_name='Danh mục'
    )
    brand = models.CharField(max_length=255, blank=True, verbose_name='Thương hiệu')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Trạng thái')
    stock_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)], verbose_name='Số lượng tồn')
    low_stock_threshold = models.IntegerField(default=10, verbose_name='Ngưỡng tồn kho thấp')
    weight = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Cân nặng (kg)')
    is_featured = models.BooleanField(default=False, verbose_name='Nổi bật')
    view_count = models.IntegerField(default=0, verbose_name='Lượt xem')
    sold_count = models.IntegerField(default=0, verbose_name='Đã bán')
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0, verbose_name='Đánh giá trung bình')
    rating_count = models.IntegerField(default=0, verbose_name='Số lượt đánh giá')
    seller_id = models.UUIDField(blank=True, null=True, verbose_name='ID người bán')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ngày cập nhật')

    class Meta:
        db_table = 'products'
        verbose_name = 'Sản phẩm'
        verbose_name_plural = 'Sản phẩm'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'category']),
            models.Index(fields=['price']),
            models.Index(fields=['-sold_count']),
            models.Index(fields=['-rating_avg']),
        ]

    def __str__(self):
        return self.name

    @property
    def is_on_sale(self):
        return self.compare_price and self.compare_price > self.price

    @property
    def discount_percent(self):
        if self.is_on_sale:
            return int((1 - self.price / self.compare_price) * 100)
        return 0

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold


class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name='Sản phẩm')
    image = models.ImageField(upload_to='products/', verbose_name='Hình ảnh')
    alt_text = models.CharField(max_length=255, blank=True, verbose_name='Text thay thế')
    is_primary = models.BooleanField(default=False, verbose_name='Ảnh chính')
    display_order = models.IntegerField(default=0, verbose_name='Thứ tự')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')

    class Meta:
        db_table = 'product_images'
        verbose_name = 'Hình ảnh sản phẩm'
        verbose_name_plural = 'Hình ảnh sản phẩm'
        ordering = ['display_order']

    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductVariant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name='Sản phẩm')
    name = models.CharField(max_length=255, verbose_name='Tên biến thể')
    sku = models.CharField(max_length=100, unique=True, verbose_name='Mã SKU')
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='Giá')
    stock_quantity = models.IntegerField(default=0, verbose_name='Số lượng tồn')
    attributes = models.JSONField(default=dict, verbose_name='Thuộc tính')
    is_active = models.BooleanField(default=True, verbose_name='Hoạt động')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')

    class Meta:
        db_table = 'product_variants'
        verbose_name = 'Biến thể sản phẩm'
        verbose_name_plural = 'Biến thể sản phẩm'

    def __str__(self):
        return f"{self.product.name} - {self.name}"
