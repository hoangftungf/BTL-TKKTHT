"""
Product Signals — sử dụng Domain Event Bus thay vì daemon threads.

Khi Product thay đổi, publish event thay vì thread gọi HTTP tới chatbot.
Nếu RabbitMQ không available, fallback log + cache clear.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from decimal import Decimal
import logging

from .models import Product, ProductImage, ProductVariant, Category
from lib.shared.domain_events import ProductUpdated, ProductDeleted, EventBus

logger = logging.getLogger(__name__)


def serialize_product(product: Product) -> dict:
    """Serialize Product model thành dict để publish qua EventBus."""
    category_name = product.category.name if product.category else None

    # Get first image
    image_url = ""
    first_img = product.images.filter(is_primary=True).first() or product.images.first()
    if first_img:
        image_str = str(first_img.image)
        if image_str.startswith('http:/') or image_str.startswith('https:/'):
            if not image_str.startswith('http://') and not image_str.startswith('https://'):
                image_str = image_str.replace(':/', '://', 1)
        if image_str.startswith('http://') or image_str.startswith('https://'):
            image_url = image_str
        else:
            image_url = first_img.image.url if hasattr(first_img.image, 'url') else ""

    # Serialize variants
    variants_data = []
    for v in product.variants.filter(is_active=True):
        variants_data.append({
            'id': str(v.id),
            'name': v.name,
            'sku': v.sku,
            'price': float(v.price) if v.price is not None else 0,
            'stock_quantity': v.stock_quantity,
            'attributes': v.attributes,
            'is_active': v.is_active,
        })

    return {
        'id': str(product.id),
        'name': product.name,
        'price': float(product.price),
        'brand': product.brand,
        'category': category_name,
        'description': product.description,
        'status': product.status,
        'stock_quantity': product.stock_quantity,
        'image_url': image_url,
        'specifications': product.specifications or {},
        'variants': variants_data,
    }


@receiver([post_save, post_delete], sender=Product)
def handle_product_change(sender, instance, **kwargs):
    """Publish domain event thay vì daemon thread gọi HTTP."""
    # Clear local cache
    try:
        cache.delete_pattern("product_list_*")
        cache.delete_pattern("product_detail_*")
    except Exception:
        cache.clear()

    # Publish event
    if kwargs.get('created'):
        event = ProductUpdated(serialize_product(instance))
    elif not kwargs.get('raw', False):
        event = ProductUpdated(serialize_product(instance))
    else:
        return

    EventBus.publish(event)


@receiver(post_delete, sender=Product)
def handle_product_deleted(sender, instance, **kwargs):
    """Publish product.deleted event."""
    try:
        cache.delete_pattern("product_list_*")
        cache.delete_pattern("product_detail_*")
    except Exception:
        cache.clear()

    EventBus.publish(ProductDeleted(str(instance.id)))


@receiver([post_save, post_delete], sender=ProductVariant)
def handle_variant_change(sender, instance, **kwargs):
    """Publish product.updated khi variant thay đổi."""
    try:
        cache.delete_pattern("product_list_*")
        cache.delete_pattern("product_detail_*")
    except Exception:
        cache.clear()

    if instance.product:
        EventBus.publish(ProductUpdated(serialize_product(instance.product)))


@receiver([post_save, post_delete], sender=ProductImage)
@receiver([post_save, post_delete], sender=Category)
def clear_product_cache(sender, **kwargs):
    """Clear cache khi image hoặc category thay đổi."""
    try:
        cache.delete_pattern("product_list_*")
        cache.delete_pattern("product_detail_*")
        cache.delete_pattern("category_list*")
        cache.delete_pattern("products_by_category_*")
    except Exception:
        cache.clear()
