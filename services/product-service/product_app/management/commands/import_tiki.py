"""
Django Management Command: Import Tiki Products
================================================
Imports real products from Tiki API scrape into Django DB with bilingual category mapping.

Usage:
    docker-compose exec product-service python manage.py import_tiki /data/tiki_api_products.json

Or locally:
    python manage.py import_tiki data/raw/tiki_api_products.json
"""

import json
import re
from pathlib import Path
from django.core.management.base import BaseCommand
from product_app.models import Category, Product


# Bilingual Category Mapping for Tiki data
CATEGORY_TREE = {
    # Level 1: Root categories
    'electronics': {
        'name': 'Điện tử',
        'slug': 'electronics',
        'description': 'Electronics - Thiết bị điện tử',
        'parent': None,
    },
    'fashion': {
        'name': 'Thời trang',
        'slug': 'fashion',
        'description': 'Fashion - Quần áo, giày dép',
        'parent': None,
    },

    # Level 2: Sub-categories under Electronics
    'laptop': {
        'name': 'Laptop',
        'slug': 'laptop',
        'description': 'Laptop - Máy tính xách tay',
        'parent': 'electronics',
    },
    'smartphone': {
        'name': 'Điện thoại thông minh',
        'slug': 'smartphone',
        'description': 'Smartphone - Điện thoại di động',
        'parent': 'electronics',
    },

    # Level 2: Sub-categories under Fashion
    'men-shirts': {
        'name': 'Áo nam',
        'slug': 'men-shirts',
        'description': 'Men Shirts - Áo thun, áo polo nam',
        'parent': 'fashion',
    },
    'men-shoes': {
        'name': 'Giày nam',
        'slug': 'men-shoes',
        'description': 'Men Shoes - Giày dép nam',
        'parent': 'fashion',
    },
}

# Map Tiki category_slug to our category slug
TIKI_CATEGORY_MAP = {
    'laptop': 'laptop',
    'smartphone': 'smartphone',
    'ao-thun-nam': 'men-shirts',
    'giay-dep-nam': 'men-shoes',
}


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    text = text.lower().strip()
    # Remove Vietnamese accents
    vietnamese_map = {
        'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'đ': 'd',
        'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
    }
    for vi, en in vietnamese_map.items():
        text = text.replace(vi, en)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text[:100]


class Command(BaseCommand):
    help = 'Import Tiki products into Django DB with bilingual category mapping'

    def add_arguments(self, parser):
        parser.add_argument('source', type=str, help='Path to JSON file')
        parser.add_argument('--limit', type=int, help='Limit number of products')
        parser.add_argument('--clear', action='store_true', help='Clear existing Tiki products first')

    def handle(self, *args, **options):
        source_path = Path(options['source'])
        limit = options.get('limit')
        clear = options.get('clear', False)

        # Load JSON
        self.stdout.write(f"Loading products from {source_path}...")
        with open(source_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        products = data.get('products', [])
        if limit:
            products = products[:limit]

        self.stdout.write(f"Loaded {len(products)} products")

        # Clear existing Tiki products if requested
        if clear:
            deleted, _ = Product.objects.filter(sku__startswith='TIKI-').delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted} existing Tiki products"))

        # Create categories
        self.stdout.write("Creating categories...")
        category_cache = self._create_categories()

        # Import products
        self.stdout.write("Importing products...")
        stats = self._import_products(products, category_cache)

        # Summary
        self.stdout.write(self.style.SUCCESS(f"\n{'='*50}"))
        self.stdout.write(self.style.SUCCESS(f"Import Complete!"))
        self.stdout.write(f"  Categories created: {stats['categories_created']}")
        self.stdout.write(f"  Products created: {stats['products_created']}")
        self.stdout.write(f"  Products skipped (duplicate): {stats['products_skipped']}")
        self.stdout.write(f"  Products failed: {stats['products_failed']}")
        self.stdout.write(self.style.SUCCESS(f"{'='*50}"))

        # Final counts
        total_products = Product.objects.count()
        total_categories = Category.objects.count()
        tiki_products = Product.objects.filter(sku__startswith='TIKI-').count()
        self.stdout.write(f"\nDatabase totals:")
        self.stdout.write(f"  Total products: {total_products}")
        self.stdout.write(f"  Tiki products: {tiki_products}")
        self.stdout.write(f"  Total categories: {total_categories}")

    def _create_categories(self):
        """Create category tree and return slug->instance mapping"""
        category_cache = {}
        stats = {'created': 0, 'existing': 0}

        # First pass: create all categories without parents
        for slug, info in CATEGORY_TREE.items():
            cat, created = Category.objects.get_or_create(
                slug=info['slug'],
                defaults={
                    'name': info['name'],
                    'description': info['description'],
                    'is_active': True,
                }
            )
            category_cache[slug] = cat
            if created:
                stats['created'] += 1
                self.stdout.write(f"  Created: {info['name']} ({slug})")
            else:
                stats['existing'] += 1

        # Second pass: set parent relationships
        for slug, info in CATEGORY_TREE.items():
            if info['parent']:
                cat = category_cache[slug]
                parent = category_cache.get(info['parent'])
                if parent and cat.parent_id != parent.id:
                    cat.parent = parent
                    cat.save(update_fields=['parent'])

        self.stdout.write(f"  Categories: {stats['created']} created, {stats['existing']} existing")
        return category_cache

    def _import_products(self, products, category_cache):
        """Import products and return stats"""
        stats = {
            'categories_created': 0,
            'products_created': 0,
            'products_skipped': 0,
            'products_failed': 0,
        }

        # Get existing SKUs
        existing_skus = set(Product.objects.filter(
            sku__startswith='TIKI-'
        ).values_list('sku', flat=True))

        for i, product in enumerate(products):
            sku = f"TIKI-{product.get('source_id', i)}"

            # Skip duplicates
            if sku in existing_skus:
                stats['products_skipped'] += 1
                continue

            # Get category
            tiki_cat_slug = product.get('category_slug', '')
            our_cat_slug = TIKI_CATEGORY_MAP.get(tiki_cat_slug, tiki_cat_slug)
            category = category_cache.get(our_cat_slug)

            # Generate unique slug
            base_slug = slugify(product['name'])
            product_slug = base_slug
            counter = 1
            while Product.objects.filter(slug=product_slug).exists():
                product_slug = f"{base_slug}-{counter}"
                counter += 1

            try:
                Product.objects.create(
                    name=product['name'],
                    slug=product_slug,
                    sku=sku,
                    price=product['price'],
                    compare_price=product.get('original_price'),
                    brand=product.get('brand', ''),
                    description=f"Sản phẩm từ Tiki. Rating: {product.get('rating', 0)}, Đã bán: {product.get('sold', 0)}",
                    short_description=product['name'][:200],
                    stock_quantity=100,
                    is_featured=product.get('sold', 0) > 10,
                    status='active',
                    category=category,
                )
                stats['products_created'] += 1
                existing_skus.add(sku)

                if (i + 1) % 20 == 0:
                    self.stdout.write(f"  Progress: {i+1}/{len(products)}")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Failed: {product['name'][:50]} - {e}"))
                stats['products_failed'] += 1

        return stats
