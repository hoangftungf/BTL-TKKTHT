from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
import threading
import httpx
import logging
from .models import Product, ProductImage, ProductVariant, Category

logger = logging.getLogger(__name__)

def notify_chatbot_async(product_id):
    try:
        product = Product.objects.get(id=product_id)
        category_name = product.category.name if product.category else None
        
        # Get first image if available
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
                'is_active': v.is_active
            })

        payload = {
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
            'variants': variants_data
        }
        
        # Call the chatbot service update endpoint
        import os
        chatbot_url = os.environ.get('AI_CHATBOT_URL', 'http://ai-chatbot:8000')
        resp = httpx.post(f"{chatbot_url}/api/chatbot/update-product/", json=payload, timeout=5.0)
        logger.info(f"Notified chatbot service for product {product_id}, status: {resp.status_code}")
    except Exception as e:
        logger.error(f"Failed to notify chatbot service for product {product_id}: {e}")

@receiver([post_save, post_delete], sender=Product)
def handle_product_change(sender, instance, **kwargs):
    # Clear local cache
    try:
        cache.delete_pattern("product_list_*")
        cache.delete_pattern("product_detail_*")
    except Exception:
        cache.clear()
        
    # Trigger non-blocking notify thread if it was a save
    if kwargs.get('created') or not kwargs.get('raw', False):
        thread = threading.Thread(target=notify_chatbot_async, args=(instance.id,))
        thread.daemon = True
        thread.start()

@receiver([post_save, post_delete], sender=ProductVariant)
def handle_variant_change(sender, instance, **kwargs):
    # Clear local cache
    try:
        cache.delete_pattern("product_list_*")
        cache.delete_pattern("product_detail_*")
    except Exception:
        cache.clear()
        
    # Trigger non-blocking notify thread for parent product
    if instance.product:
        thread = threading.Thread(target=notify_chatbot_async, args=(instance.product.id,))
        thread.daemon = True
        thread.start()

@receiver([post_save, post_delete], sender=ProductImage)
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

