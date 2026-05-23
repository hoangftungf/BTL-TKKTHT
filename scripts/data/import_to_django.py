"""
Django Data Importer
====================
Imports normalized product data into Django database.

Usage:
    # From project root, with Django settings
    cd services/product-service
    python ../../scripts/data/import_to_django.py \
        --source ../../data/processed/tiki_normalized.json \
        --dataset-tag real_tiki

    # Or import all processed files
    python ../../scripts/data/import_to_django.py \
        --source-dir ../../data/processed/ \
        --clear-existing
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'product_project.settings')

# Add the product-service to path
service_path = os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'product-service')
sys.path.insert(0, os.path.abspath(service_path))

import django
django.setup()

from django.db import transaction
from product_app.models import Category, Product

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class DjangoImporter:
    """Import normalized products into Django"""

    def __init__(self):
        self.categories_cache = {}
        self.stats = {
            'categories_created': 0,
            'categories_updated': 0,
            'products_created': 0,
            'products_updated': 0,
            'products_skipped': 0
        }

    def clear_existing(self):
        """Clear all products and categories"""
        logger.warning("Clearing existing data...")
        Product.objects.all().delete()
        Category.objects.all().delete()
        logger.info("Cleared all products and categories")

    def load_category_mapping(self, mapping_file: str):
        """Load category mapping and create categories in Django"""
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping = json.load(f)

        self._create_categories_recursive(mapping['categories'], parent=None)
        logger.info(f"Created {self.stats['categories_created']} categories")

    def _create_categories_recursive(self, categories: list, parent: Category = None, order: int = 0):
        """Recursively create category tree"""
        for i, cat_data in enumerate(categories):
            cat_id = cat_data['id']

            # Use English name for slug, Vietnamese for display
            slug = cat_data['slug']
            name = cat_data['name_vi']  # Display name in Vietnamese

            category, created = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'description': f"{cat_data['name_en']} - {name}",
                    'parent': parent,
                    'is_active': True,
                    'display_order': order + i
                }
            )

            if created:
                self.stats['categories_created'] += 1
            else:
                self.stats['categories_updated'] += 1

            # Cache for product import
            self.categories_cache[cat_id] = category
            self.categories_cache[slug] = category

            # Process children
            if cat_data.get('children'):
                self._create_categories_recursive(cat_data['children'], parent=category, order=0)

    def import_products(self, filepath: str, dataset_tag: str = None):
        """Import products from normalized JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        products = data.get('products', [])
        logger.info(f"Importing {len(products)} products from {filepath}")

        with transaction.atomic():
            for i, p in enumerate(products):
                try:
                    self._import_product(p, dataset_tag)

                    if (i + 1) % 100 == 0:
                        logger.info(f"  Processed {i + 1}/{len(products)}")

                except Exception as e:
                    logger.warning(f"Error importing product {p.get('name', 'unknown')}: {e}")
                    self.stats['products_skipped'] += 1

        logger.info(f"Import complete: {self.stats['products_created']} created, "
                   f"{self.stats['products_updated']} updated, "
                   f"{self.stats['products_skipped']} skipped")

    def _import_product(self, p: dict, dataset_tag: str = None):
        """Import single product"""
        # Find category
        category = None
        cat_id = p.get('category_id')
        cat_slug = p.get('category_slug')

        if cat_id and cat_id in self.categories_cache:
            category = self.categories_cache[cat_id]
        elif cat_slug and cat_slug in self.categories_cache:
            category = self.categories_cache[cat_slug]
        else:
            # Try to find by slug
            try:
                category = Category.objects.get(slug=cat_slug)
                self.categories_cache[cat_slug] = category
            except Category.DoesNotExist:
                pass

        # Prepare product data
        sku = p.get('sku', '')
        if not sku:
            sku = f"{p.get('source', 'XX')[:2].upper()}-{abs(hash(p.get('name', ''))) % 1000000:06d}"

        # Build description with source info
        description = p.get('description', '') or ''
        if dataset_tag:
            description = f"[{dataset_tag}] {description}"

        product, created = Product.objects.update_or_create(
            sku=sku,
            defaults={
                'name': p.get('name', 'Unknown'),
                'slug': p.get('slug', sku.lower()),
                'price': Decimal(str(p.get('price', 0))),
                'compare_price': Decimal(str(p['compare_price'])) if p.get('compare_price') else None,
                'brand': p.get('brand', ''),
                'description': description,
                'short_description': p.get('short_description', '')[:500] if p.get('short_description') else '',
                'stock_quantity': p.get('stock_quantity', 100),
                'is_featured': p.get('is_featured', False),
                'status': p.get('status', 'active'),
                'category': category,
                'rating_avg': Decimal(str(p.get('rating_avg', 0) or 0)),
                'rating_count': p.get('rating_count', 0) or 0,
                'sold_count': p.get('sold_count', 0) or 0,
            }
        )

        if created:
            self.stats['products_created'] += 1
        else:
            self.stats['products_updated'] += 1

    def import_from_directory(self, dir_path: str):
        """Import all normalized JSON files from directory"""
        for filename in os.listdir(dir_path):
            if filename.endswith('_normalized.json'):
                filepath = os.path.join(dir_path, filename)

                # Extract dataset tag from filename
                dataset_tag = filename.replace('_normalized.json', '')

                logger.info(f"\n{'='*50}")
                logger.info(f"Importing: {filename} (tag: {dataset_tag})")
                logger.info(f"{'='*50}")

                self.import_products(filepath, dataset_tag)


def main():
    parser = argparse.ArgumentParser(description='Import products into Django')
    parser.add_argument('--source', '-s', type=str, help='Source JSON file')
    parser.add_argument('--source-dir', '-d', type=str, help='Directory with normalized JSON files')
    parser.add_argument('--category-map', '-c',
                        default='scripts/data/category_mapping.json',
                        help='Category mapping file')
    parser.add_argument('--dataset-tag', '-t', type=str, help='Dataset tag for products')
    parser.add_argument('--clear-existing', action='store_true', help='Clear existing data first')

    args = parser.parse_args()

    importer = DjangoImporter()

    # Clear if requested
    if args.clear_existing:
        confirm = input("Are you sure you want to clear ALL existing data? (yes/no): ")
        if confirm.lower() == 'yes':
            importer.clear_existing()
        else:
            logger.info("Aborted.")
            return

    # Load categories
    if os.path.exists(args.category_map):
        logger.info(f"Loading categories from {args.category_map}")
        importer.load_category_mapping(args.category_map)
    else:
        logger.warning(f"Category mapping not found: {args.category_map}")

    # Import products
    if args.source:
        importer.import_products(args.source, args.dataset_tag)
    elif args.source_dir:
        importer.import_from_directory(args.source_dir)
    else:
        logger.error("Please specify --source or --source-dir")
        return

    # Print summary
    print(f"\n{'='*50}")
    print("IMPORT SUMMARY")
    print(f"{'='*50}")
    print(f"Categories created: {importer.stats['categories_created']}")
    print(f"Categories updated: {importer.stats['categories_updated']}")
    print(f"Products created:   {importer.stats['products_created']}")
    print(f"Products updated:   {importer.stats['products_updated']}")
    print(f"Products skipped:   {importer.stats['products_skipped']}")
    print(f"\nTotal in DB:")
    print(f"  Categories: {Category.objects.count()}")
    print(f"  Products:   {Product.objects.count()}")


if __name__ == '__main__':
    main()
