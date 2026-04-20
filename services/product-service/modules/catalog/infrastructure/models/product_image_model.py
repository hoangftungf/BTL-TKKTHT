"""
Product Image Django ORM Model
"""
import uuid
from django.db import models

from .product_model import ProductModel


class ProductImageModel(models.Model):
    """Django ORM Model cho Product Image"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        ProductModel, on_delete=models.CASCADE,
        related_name='images', verbose_name='San pham'
    )
    image = models.ImageField(upload_to='products/', verbose_name='Hinh anh')
    alt_text = models.CharField(max_length=255, blank=True, verbose_name='Text thay the')
    is_primary = models.BooleanField(default=False, verbose_name='Anh chinh')
    display_order = models.IntegerField(default=0, verbose_name='Thu tu')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngay tao')

    class Meta:
        db_table = 'product_images'
        verbose_name = 'Hinh anh san pham'
        verbose_name_plural = 'Hinh anh san pham'
        ordering = ['display_order']
        app_label = 'catalog'

    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductImageModel.objects.filter(
                product=self.product, is_primary=True
            ).update(is_primary=False)
        super().save(*args, **kwargs)
