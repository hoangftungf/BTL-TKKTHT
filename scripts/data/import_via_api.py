"""
Import Products via REST API
=============================
Imports normalized products into the product-service via HTTP API.
Use this when services are running in Docker.

Usage:
    python scripts/data/import_via_api.py \
        --source data/processed/synthetic_large.json \
        --api-url http://localhost:8003
"""

import argparse
import json
import logging
import os
import time
import httpx
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class APIImporter:
    """Import products via REST API"""

    def __init__(self, api_url: str, auth_token: Optional[str] = None):
        self.api_url = api_url.rstrip('/')
        self.auth_token = auth_token
        self.headers = {'Content-Type': 'application/json'}
        if auth_token:
            self.headers['Authorization'] = f'Bearer {auth_token}'

        self.stats = {
            'categories_created': 0,
            'products_created': 0,
            'products_failed': 0
        }
        self.category_cache: Dict[str, str] = {}  # slug -> id

    def get_existing_categories(self):
        """Fetch existing categories from API"""
        try:
            resp = httpx.get(f'{self.api_url}/categories/', headers=self.headers, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                categories = data.get('results', data) if isinstance(data, dict) else data
                for cat in categories:
                    self.category_cache[cat['slug']] = cat['id']
                logger.info(f"Loaded {len(self.category_cache)} existing categories")
        except Exception as e:
            logger.warning(f"Could not fetch categories: {e}")

    def create_category(self, cat_data: dict) -> Optional[str]:
        """Create a category and return its ID"""
        slug = cat_data.get('category_slug', '')
        if slug in self.category_cache:
            return self.category_cache[slug]

        payload = {
            'name': cat_data.get('category_name_vi', cat_data.get('category_name_en', 'Unknown')),
            'slug': slug,
            'description': cat_data.get('category_name_en', ''),
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
                self.category_cache[slug] = cat_id
                self.stats['categories_created'] += 1
                return cat_id
            elif resp.status_code == 400:
                # Might already exist, try to get it
                self.get_existing_categories()
                return self.category_cache.get(slug)
        except Exception as e:
            logger.warning(f"Failed to create category {slug}: {e}")

        return None

    def create_product(self, product: dict) -> bool:
        """Create a single product via API"""
        # Ensure category exists
        cat_id = None
        if product.get('category_slug'):
            cat_id = self.create_category(product)

        payload = {
            'name': product['name'],
            'slug': product['slug'],
            'sku': product['sku'],
            'price': str(product['price']),
            'compare_price': str(product['compare_price']) if product.get('compare_price') else None,
            'brand': product.get('brand', ''),
            'description': product.get('description', ''),
            'short_description': product.get('short_description', ''),
            'stock_quantity': product.get('stock_quantity', 100),
            'is_featured': product.get('is_featured', False),
            'status': product.get('status', 'active'),
            'category': cat_id
        }

        try:
            resp = httpx.post(
                f'{self.api_url}/products/',
                json=payload,
                headers=self.headers,
                timeout=30
            )
            if resp.status_code in (200, 201):
                self.stats['products_created'] += 1
                return True
            else:
                logger.debug(f"Failed to create {product['name']}: {resp.status_code} - {resp.text[:200]}")
                self.stats['products_failed'] += 1
                return False
        except Exception as e:
            logger.warning(f"Error creating product: {e}")
            self.stats['products_failed'] += 1
            return False

    def import_products(self, products: List[dict]):
        """Import all products"""
        total = len(products)
        logger.info(f"Importing {total} products...")

        for i, product in enumerate(products):
            self.create_product(product)

            if (i + 1) % 50 == 0:
                logger.info(f"Progress: {i+1}/{total} ({(i+1)*100//total}%)")
                time.sleep(0.1)  # Small delay to avoid overwhelming the server

        logger.info(f"\nImport complete!")
        logger.info(f"  Categories created: {self.stats['categories_created']}")
        logger.info(f"  Products created: {self.stats['products_created']}")
        logger.info(f"  Products failed: {self.stats['products_failed']}")


def main():
    parser = argparse.ArgumentParser(description='Import products via API')
    parser.add_argument('--source', '-s', required=True, help='Source JSON file')
    parser.add_argument('--api-url', '-u', default='http://localhost:8003', help='Product service URL')
    parser.add_argument('--token', '-t', help='Auth token (optional)')
    parser.add_argument('--limit', '-l', type=int, help='Limit number of products')

    args = parser.parse_args()

    # Load products
    with open(args.source, 'r', encoding='utf-8') as f:
        data = json.load(f)

    products = data.get('products', [])
    if args.limit:
        products = products[:args.limit]

    logger.info(f"Loaded {len(products)} products from {args.source}")

    # Import
    importer = APIImporter(args.api_url, args.token)
    importer.get_existing_categories()
    importer.import_products(products)


if __name__ == '__main__':
    main()
