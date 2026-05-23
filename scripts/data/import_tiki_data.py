"""
Import Tiki Products to Django DB via API
==========================================
Imports real products from Tiki API scrape into Django with bilingual category mapping.

Usage:
    python scripts/data/import_tiki_data.py --api-url http://localhost:8003
"""

import argparse
import json
import logging
import os
import re
import time
import httpx
from typing import Dict, List, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Bilingual Category Mapping for Tiki data
# Structure: source_slug -> {name_vi, name_en, slug, parent_slug}
CATEGORY_MAPPING = {
    # Level 1: Root categories
    'dien-tu': {
        'name_vi': 'Điện tử',
        'name_en': 'Electronics',
        'slug': 'electronics',
        'parent_slug': None
    },
    'thoi-trang': {
        'name_vi': 'Thời trang',
        'name_en': 'Fashion',
        'slug': 'fashion',
        'parent_slug': None
    },

    # Level 2: Sub-categories
    'laptop': {
        'name_vi': 'Laptop',
        'name_en': 'Laptop',
        'slug': 'laptop',
        'parent_slug': 'electronics'
    },
    'smartphone': {
        'name_vi': 'Điện thoại thông minh',
        'name_en': 'Smartphone',
        'slug': 'smartphone',
        'parent_slug': 'electronics'
    },
    'ao-thun-nam': {
        'name_vi': 'Áo nam',
        'name_en': 'Men Shirts',
        'slug': 'men-shirts',
        'parent_slug': 'fashion'
    },
    'giay-dep-nam': {
        'name_vi': 'Giày nam',
        'name_en': 'Men Shoes',
        'slug': 'men-shoes',
        'parent_slug': 'fashion'
    },
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
    # Replace spaces and special chars with hyphens
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text[:100]


class TikiImporter:
    """Import Tiki products via REST API"""

    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip('/')
        self.headers = {'Content-Type': 'application/json'}
        self.stats = {
            'categories_created': 0,
            'products_created': 0,
            'products_skipped': 0,
            'products_failed': 0
        }
        self.category_cache: Dict[str, int] = {}  # slug -> id
        self.existing_skus: set = set()

    def get_existing_data(self):
        """Fetch existing categories and products"""
        # Get categories
        try:
            resp = httpx.get(f'{self.api_url}/categories/', timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                categories = data.get('results', data) if isinstance(data, dict) else data
                for cat in categories:
                    self.category_cache[cat['slug']] = cat['id']
                logger.info(f"Loaded {len(self.category_cache)} existing categories")
        except Exception as e:
            logger.warning(f"Could not fetch categories: {e}")

        # Get existing product SKUs to avoid duplicates
        try:
            resp = httpx.get(f'{self.api_url}/?page_size=1000', timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                products = data.get('results', data) if isinstance(data, dict) else data
                for p in products:
                    if p.get('sku'):
                        self.existing_skus.add(p['sku'])
                logger.info(f"Loaded {len(self.existing_skus)} existing product SKUs")
        except Exception as e:
            logger.warning(f"Could not fetch products: {e}")

    def create_category(self, slug: str) -> Optional[int]:
        """Create or get category by slug"""
        if slug in self.category_cache:
            return self.category_cache[slug]

        mapping = CATEGORY_MAPPING.get(slug)
        if not mapping:
            logger.warning(f"No mapping for category: {slug}")
            return None

        # First create parent if needed
        parent_id = None
        if mapping['parent_slug']:
            parent_id = self.create_category(mapping['parent_slug'])

        payload = {
            'name': mapping['name_vi'],
            'slug': mapping['slug'],
            'description': mapping['name_en'],
            'parent': parent_id,
            'is_active': True
        }

        try:
            resp = httpx.post(
                f'{self.api_url}/categories/',
                json=payload,
                headers=self.headers,
                timeout=30
            )
            if resp.status_code in (200, 201):
                cat_id = resp.json().get('id')
                self.category_cache[mapping['slug']] = cat_id
                self.stats['categories_created'] += 1
                logger.info(f"Created category: {mapping['name_vi']} ({mapping['slug']})")
                return cat_id
            elif resp.status_code == 400:
                # Might already exist
                self.get_existing_data()
                return self.category_cache.get(mapping['slug'])
        except Exception as e:
            logger.warning(f"Failed to create category {slug}: {e}")

        return None

    def create_product(self, product: dict) -> bool:
        """Create a single product via API"""
        # Generate SKU from source_id
        sku = f"TIKI-{product.get('source_id', '')}"

        # Skip if already exists
        if sku in self.existing_skus:
            self.stats['products_skipped'] += 1
            return False

        # Get category
        source_slug = product.get('category_slug', '')
        mapping = CATEGORY_MAPPING.get(source_slug, {})
        target_slug = mapping.get('slug', source_slug)
        cat_id = self.category_cache.get(target_slug)

        if not cat_id and source_slug:
            cat_id = self.create_category(source_slug)

        # Generate product slug
        product_slug = slugify(product['name'])

        # Build payload
        payload = {
            'name': product['name'],
            'slug': product_slug,
            'sku': sku,
            'price': str(product['price']),
            'compare_price': str(product.get('original_price')) if product.get('original_price') else None,
            'brand': product.get('brand', ''),
            'description': f"Sản phẩm từ Tiki. Rating: {product.get('rating', 0)}, Đã bán: {product.get('sold', 0)}",
            'short_description': product['name'][:200],
            'stock_quantity': 100,
            'is_featured': product.get('sold', 0) > 10,
            'status': 'active',
            'category': cat_id
        }

        try:
            resp = httpx.post(
                f'{self.api_url}/',
                json=payload,
                headers=self.headers,
                timeout=30
            )
            if resp.status_code in (200, 201):
                self.stats['products_created'] += 1
                self.existing_skus.add(sku)
                return True
            else:
                logger.debug(f"Failed to create {product['name'][:50]}: {resp.status_code}")
                self.stats['products_failed'] += 1
                return False
        except Exception as e:
            logger.warning(f"Error creating product: {e}")
            self.stats['products_failed'] += 1
            return False

    def import_products(self, products: List[dict]):
        """Import all products"""
        total = len(products)
        logger.info(f"Importing {total} Tiki products...")

        # First ensure all parent categories exist
        for slug in ['dien-tu', 'thoi-trang']:
            self.create_category(slug)

        for i, product in enumerate(products):
            self.create_product(product)

            if (i + 1) % 20 == 0:
                logger.info(f"Progress: {i+1}/{total} ({(i+1)*100//total}%)")
                time.sleep(0.05)  # Small delay

        logger.info(f"\n{'='*50}")
        logger.info(f"Import complete!")
        logger.info(f"  Categories created: {self.stats['categories_created']}")
        logger.info(f"  Products created: {self.stats['products_created']}")
        logger.info(f"  Products skipped (duplicate): {self.stats['products_skipped']}")
        logger.info(f"  Products failed: {self.stats['products_failed']}")
        logger.info(f"{'='*50}")


def main():
    parser = argparse.ArgumentParser(description='Import Tiki products via API')
    parser.add_argument('--source', '-s',
                        default='data/raw/tiki_api_products.json',
                        help='Source JSON file')
    parser.add_argument('--api-url', '-u',
                        default='http://localhost:8003',
                        help='Product service URL')
    parser.add_argument('--limit', '-l', type=int, help='Limit number of products')

    args = parser.parse_args()

    # Resolve path
    source_path = Path(args.source)
    if not source_path.is_absolute():
        source_path = Path(__file__).parent.parent.parent / args.source

    # Load products
    with open(source_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    products = data.get('products', [])
    if args.limit:
        products = products[:args.limit]

    logger.info(f"Loaded {len(products)} products from {source_path}")

    # Import
    importer = TikiImporter(args.api_url)
    importer.get_existing_data()
    importer.import_products(products)


if __name__ == '__main__':
    main()
