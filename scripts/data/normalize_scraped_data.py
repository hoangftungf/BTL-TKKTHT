"""
Data Normalization Script
=========================
Normalizes scraped data from Tiki/Shopee into a unified format for Django import.

Usage:
    python scripts/data/normalize_scraped_data.py \
        --tiki data/raw/tiki_products.json \
        --shopee data/raw/shopee_products.json \
        --category-map scripts/data/category_mapping.json \
        --output data/processed/

Output:
    - data/processed/tiki_normalized.json
    - data/processed/shopee_normalized.json
    - data/processed/all_products_normalized.json
"""

import argparse
import json
import logging
import os
import re
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from unidecode import unidecode  # pip install unidecode

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class NormalizedProduct:
    """Unified product format for Django import"""
    id: str  # UUID
    name: str
    slug: str
    sku: str
    price: int
    compare_price: Optional[int]
    brand: str
    description: str
    short_description: str
    stock_quantity: int
    is_featured: bool
    status: str  # 'active', 'draft', 'inactive'

    # Category info (bilingual)
    category_id: str
    category_name_vi: str
    category_name_en: str
    category_slug: str
    category_level: int

    # Source info
    source: str  # 'tiki', 'shopee', 'synthetic'
    source_id: str
    source_url: str

    # Media
    image_url: Optional[str]

    # Stats
    rating_avg: float
    rating_count: int
    sold_count: int

    # Metadata
    dataset_tag: str  # 'real_tiki', 'real_shopee', 'synthetic_small', 'synthetic_large'
    normalized_at: str


class CategoryMapper:
    """Maps source categories to our bilingual category system"""

    def __init__(self, mapping_file: str):
        with open(mapping_file, 'r', encoding='utf-8') as f:
            self.mapping_data = json.load(f)

        # Build flat lookup by category ID
        self.categories_by_id: Dict[str, Dict] = {}
        self._flatten_categories(self.mapping_data['categories'])

        # Build reverse lookup from source category names
        self.tiki_mapping = self.mapping_data.get('tiki_category_mapping', {})
        self.shopee_mapping = self.mapping_data.get('shopee_category_mapping', {})

    def _flatten_categories(self, categories: List[Dict], parent_path: List[str] = None):
        """Recursively flatten category tree"""
        parent_path = parent_path or []

        for cat in categories:
            cat_id = cat['id']
            self.categories_by_id[cat_id] = {
                'id': cat_id,
                'name_vi': cat['name_vi'],
                'name_en': cat['name_en'],
                'slug': cat['slug'],
                'level': cat['level'],
                'keywords_vi': cat.get('keywords_vi', []),
                'keywords_en': cat.get('keywords_en', []),
                'parent_path': parent_path.copy()
            }

            if cat.get('children'):
                self._flatten_categories(cat['children'], parent_path + [cat_id])

    def find_category(self, source: str, source_category: str, mapped_id: Optional[str] = None) -> Dict:
        """Find matching category in our system"""
        # 1. Try direct mapped_id if provided
        if mapped_id and mapped_id in self.categories_by_id:
            return self.categories_by_id[mapped_id]

        # 2. Try source-specific mapping
        mapping = self.tiki_mapping if source == 'tiki' else self.shopee_mapping
        for source_name, cat_id in mapping.items():
            if source_name.lower() in source_category.lower() or source_category.lower() in source_name.lower():
                if cat_id in self.categories_by_id:
                    return self.categories_by_id[cat_id]

        # 3. Try keyword matching
        source_lower = unidecode(source_category.lower())
        best_match = None
        best_score = 0

        for cat_id, cat_info in self.categories_by_id.items():
            score = 0
            keywords = cat_info['keywords_vi'] + cat_info['keywords_en']

            for kw in keywords:
                kw_lower = unidecode(kw.lower())
                if kw_lower in source_lower or source_lower in kw_lower:
                    score += 1

            if score > best_score:
                best_score = score
                best_match = cat_info

        if best_match:
            return best_match

        # 4. Default to generic category
        logger.warning(f"No category match for '{source_category}' from {source}")
        return {
            'id': 'cat_other',
            'name_vi': 'Khac',
            'name_en': 'Other',
            'slug': 'other',
            'level': 0
        }


class DataNormalizer:
    """Normalizes product data from various sources"""

    def __init__(self, category_mapper: CategoryMapper):
        self.mapper = category_mapper
        self.seen_skus = set()

    def normalize_tiki(self, raw_data: Dict) -> List[NormalizedProduct]:
        """Normalize Tiki scraped data"""
        products = []
        raw_products = raw_data.get('products', [])

        for item in raw_products:
            try:
                product = self._normalize_product(item, 'tiki', 'real_tiki')
                if product:
                    products.append(product)
            except Exception as e:
                logger.warning(f"Error normalizing Tiki product: {e}")

        logger.info(f"Normalized {len(products)} Tiki products")
        return products

    def normalize_shopee(self, raw_data: Dict) -> List[NormalizedProduct]:
        """Normalize Shopee scraped data"""
        products = []
        raw_products = raw_data.get('products', [])

        for item in raw_products:
            try:
                product = self._normalize_product(item, 'shopee', 'real_shopee')
                if product:
                    products.append(product)
            except Exception as e:
                logger.warning(f"Error normalizing Shopee product: {e}")

        logger.info(f"Normalized {len(products)} Shopee products")
        return products

    def _normalize_product(self, item: Dict, source: str, dataset_tag: str) -> Optional[NormalizedProduct]:
        """Normalize single product"""
        name = item.get('name', '').strip()
        if not name:
            return None

        price = int(item.get('price', 0))
        if price <= 0:
            return None

        # Generate unique SKU
        source_id = str(item.get('source_id', ''))
        sku = self._generate_sku(source, source_id, name)
        if sku in self.seen_skus:
            return None
        self.seen_skus.add(sku)

        # Find category
        category = self.mapper.find_category(
            source,
            item.get('category_source', ''),
            item.get('category_mapped')
        )

        # Generate slug
        slug = self._generate_slug(name)

        # Clean description
        description = self._clean_text(item.get('description', ''))
        short_desc = self._clean_text(item.get('short_description', ''))
        if not short_desc and description:
            short_desc = description[:200] + '...' if len(description) > 200 else description

        # Determine featured status (high rating + high sales)
        rating = float(item.get('rating') or 0)
        sold = int(item.get('sold_count') or 0)
        is_featured = rating >= 4.5 and sold >= 100

        return NormalizedProduct(
            id=str(uuid.uuid4()),
            name=name,
            slug=slug,
            sku=sku,
            price=price,
            compare_price=int(item.get('original_price')) if item.get('original_price') else None,
            brand=item.get('brand', '') or self._extract_brand(name),
            description=description,
            short_description=short_desc,
            stock_quantity=100,  # Default stock
            is_featured=is_featured,
            status='active',
            category_id=category['id'],
            category_name_vi=category['name_vi'],
            category_name_en=category['name_en'],
            category_slug=category['slug'],
            category_level=category['level'],
            source=source,
            source_id=source_id,
            source_url=item.get('url', ''),
            image_url=item.get('image_url'),
            rating_avg=rating,
            rating_count=int(item.get('review_count') or 0),
            sold_count=sold,
            dataset_tag=dataset_tag,
            normalized_at=datetime.now().isoformat()
        )

    def _generate_sku(self, source: str, source_id: str, name: str) -> str:
        """Generate unique SKU"""
        prefix = source[:2].upper()
        if source_id:
            return f"{prefix}-{source_id}"
        else:
            # Fallback: hash of name
            name_hash = abs(hash(name)) % 1000000
            return f"{prefix}-{name_hash:06d}"

    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug"""
        # Remove diacritics
        slug = unidecode(name.lower())
        # Replace special chars with hyphen
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        # Limit length
        if len(slug) > 100:
            slug = slug[:100].rsplit('-', 1)[0]
        return slug

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ''
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Normalize whitespace
        text = ' '.join(text.split())
        return text.strip()

    def _extract_brand(self, name: str) -> str:
        """Try to extract brand from product name"""
        known_brands = [
            'Apple', 'Samsung', 'Xiaomi', 'OPPO', 'Vivo', 'Realme', 'OnePlus',
            'Dell', 'HP', 'Lenovo', 'ASUS', 'Acer', 'MSI', 'LG',
            'Nike', 'Adidas', 'Puma', 'New Balance', 'Converse', 'Vans',
            'Zara', 'H&M', 'Uniqlo', 'Mango',
            'LOreal', 'Maybelline', 'Innisfree', 'The Face Shop', 'Senka',
            'Philips', 'Panasonic', 'Sony', 'JBL', 'Anker',
            'Sunhouse', 'Kangaroo', 'Lock&Lock'
        ]

        name_lower = name.lower()
        for brand in known_brands:
            if brand.lower() in name_lower:
                return brand

        return ''


def save_normalized(products: List[NormalizedProduct], filepath: str, dataset_name: str):
    """Save normalized products to JSON"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    data = {
        'dataset': dataset_name,
        'normalized_at': datetime.now().isoformat(),
        'total_count': len(products),
        'products': [asdict(p) for p in products]
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved {len(products)} products to {filepath}")


def main():
    parser = argparse.ArgumentParser(description='Normalize scraped product data')
    parser.add_argument('--tiki', '-t', type=str, help='Tiki raw data JSON file')
    parser.add_argument('--shopee', '-s', type=str, help='Shopee raw data JSON file')
    parser.add_argument('--category-map', '-c', required=True,
                        help='Category mapping JSON file')
    parser.add_argument('--output', '-o', default='data/processed/',
                        help='Output directory')

    args = parser.parse_args()

    # Initialize mapper
    mapper = CategoryMapper(args.category_map)
    normalizer = DataNormalizer(mapper)

    all_products = []

    # Process Tiki data
    if args.tiki and os.path.exists(args.tiki):
        logger.info(f"Processing Tiki data from {args.tiki}")
        with open(args.tiki, 'r', encoding='utf-8') as f:
            tiki_raw = json.load(f)
        tiki_products = normalizer.normalize_tiki(tiki_raw)
        save_normalized(tiki_products, os.path.join(args.output, 'tiki_normalized.json'), 'real_tiki')
        all_products.extend(tiki_products)

    # Process Shopee data
    if args.shopee and os.path.exists(args.shopee):
        logger.info(f"Processing Shopee data from {args.shopee}")
        with open(args.shopee, 'r', encoding='utf-8') as f:
            shopee_raw = json.load(f)
        shopee_products = normalizer.normalize_shopee(shopee_raw)
        save_normalized(shopee_products, os.path.join(args.output, 'shopee_normalized.json'), 'real_shopee')
        all_products.extend(shopee_products)

    # Save combined
    if all_products:
        save_normalized(all_products, os.path.join(args.output, 'all_products_normalized.json'), 'combined')

    # Print summary
    print(f"\n{'='*60}")
    print("NORMALIZATION COMPLETE")
    print(f"{'='*60}")
    print(f"Total products: {len(all_products)}")

    # Category breakdown
    cat_counts = {}
    for p in all_products:
        cat_counts[p.category_name_en] = cat_counts.get(p.category_name_en, 0) + 1

    print("\nBy category:")
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")


if __name__ == '__main__':
    main()
