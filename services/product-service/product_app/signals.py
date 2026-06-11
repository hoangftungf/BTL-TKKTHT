from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Product, ProductImage, ProductVariant, Category

@receiver([post_save, post_delete], sender=Product)
@receiver([post_save, post_delete], sender=ProductImage)
@receiver([post_save, post_delete], sender=ProductVariant)
@receiver([post_save, post_delete], sender=Category)
def clear_product_cache(sender, **kwargs):
    try:
        # django-redis specific delete_pattern
        cache.delete_pattern("product_list_*")
        cache.delete_pattern("product_detail_*")
        cache.delete_pattern("category_list*")
        cache.delete_pattern("products_by_category_*")
    except Exception:
        # Fallback to clear all cache if delete_pattern fails
        cache.clear()
