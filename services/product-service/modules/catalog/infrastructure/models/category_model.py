"""
Category Django ORM Model
Infrastructure layer - phu thuoc Django framework
"""
import uuid
from django.db import models


class CategoryModel(models.Model):
    """Django ORM Model cho Category"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name='Ten danh muc')
    slug = models.SlugField(max_length=255, unique=True, verbose_name='Slug')
    description = models.TextField(blank=True, verbose_name='Mo ta')
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name='Hinh anh')
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, blank=True, null=True,
        related_name='children', verbose_name='Danh muc cha'
    )
    is_active = models.BooleanField(default=True, verbose_name='Hoat dong')
    display_order = models.IntegerField(default=0, verbose_name='Thu tu hien thi')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngay tao')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ngay cap nhat')

    class Meta:
        db_table = 'categories'
        verbose_name = 'Danh muc'
        verbose_name_plural = 'Danh muc'
        ordering = ['display_order', 'name']
        app_label = 'catalog'

    def __str__(self):
        return self.name
