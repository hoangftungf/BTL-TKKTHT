import uuid
from django.db import models
from django.core.validators import MinValueValidator


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(unique=True, verbose_name='ID người dùng')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carts'

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items.all())


class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product_id = models.UUIDField(verbose_name='ID sản phẩm')
    variant_id = models.UUIDField(blank=True, null=True, verbose_name='ID biến thể')
    product_name = models.CharField(max_length=255, verbose_name='Tên sản phẩm')
    product_image = models.URLField(blank=True, verbose_name='Hình ảnh')
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='Giá')
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)], verbose_name='Số lượng')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart_items'
        unique_together = ['cart', 'product_id', 'variant_id']

    @property
    def subtotal(self):
        return self.price * self.quantity
