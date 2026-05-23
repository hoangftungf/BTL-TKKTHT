"""
Synthetic Large Dataset Generator
=================================
Generates a large synthetic dataset (500+ products) for evaluation.

Usage:
    python scripts/data/generate_synthetic_large.py \
        --output data/processed/synthetic_large.json \
        --count 500

This creates diverse products across all categories with realistic
Vietnamese product names, prices, and descriptions.
"""

import argparse
import json
import os
import random
import re
import uuid
from datetime import datetime
from typing import List, Dict

# Product templates by category
PRODUCT_TEMPLATES = {
    'cat_laptop': {
        'brands': ['Dell', 'HP', 'Lenovo', 'ASUS', 'Acer', 'MSI', 'Apple', 'LG', 'Huawei'],
        'models': [
            'XPS {n}', 'Inspiron {n}', 'Latitude {n}',
            'Pavilion {n}', 'Envy {n}', 'Spectre x360',
            'ThinkPad X1 Carbon', 'IdeaPad {n}', 'Legion {n}',
            'ROG Strix G{n}', 'ZenBook {n}', 'VivoBook {n}',
            'Aspire {n}', 'Swift {n}', 'Nitro {n}',
            'Katana GF{n}', 'Stealth {n}', 'Creator {n}',
            'MacBook Pro {n}', 'MacBook Air M{n}',
            'Gram {n}', 'MateBook D{n}'
        ],
        'specs': ['Core i5', 'Core i7', 'Core i9', 'Ryzen 5', 'Ryzen 7', 'M2', 'M3', 'M3 Pro'],
        'ram': ['8GB', '16GB', '32GB'],
        'storage': ['256GB SSD', '512GB SSD', '1TB SSD'],
        'price_range': (12000000, 60000000),
        'name_template': '{brand} {model} {spec} {ram} {storage}',
        'desc_template': 'Laptop {brand} {model} voi chip {spec}, {ram} RAM, {storage}. Thiet ke mong nhe, pin lau, phu hop cho {use_case}.'
    },
    'cat_smartphone': {
        'brands': ['Samsung', 'Apple', 'Xiaomi', 'OPPO', 'Vivo', 'Realme', 'OnePlus', 'Google', 'Nothing'],
        'models': [
            'Galaxy S{n} Ultra', 'Galaxy S{n}+', 'Galaxy A{n}', 'Galaxy Z Fold{n}',
            'iPhone {n} Pro Max', 'iPhone {n} Pro', 'iPhone {n}',
            '{n} Ultra', '{n} Pro', 'Redmi Note {n}',
            'Find X{n}', 'Reno {n}', 'A{n}',
            'X{n} Pro', 'V{n}',
            '{n} Pro+', 'GT {n}',
            '{n}T', '{n} Pro',
            'Pixel {n} Pro', 'Pixel {n}a',
            'Phone ({n})'
        ],
        'storage': ['128GB', '256GB', '512GB', '1TB'],
        'price_range': (3000000, 40000000),
        'name_template': '{brand} {model} {storage}',
        'desc_template': 'Dien thoai {brand} {model} dung luong {storage}, man hinh AMOLED, camera AI, sac nhanh, {feature}.'
    },
    'cat_shirt_men': {
        'brands': ['Coolmate', 'Uniqlo', 'H&M', 'Zara', 'Local Brand', 'Aristino', 'Owen', 'Viet Tien'],
        'types': ['Ao thun', 'Ao polo', 'Ao so mi', 'Ao khoac', 'Hoodie', 'Sweater'],
        'materials': ['Cotton', 'Cotton Premium', 'Polyester', 'Linen', 'Bamboo'],
        'colors': ['Trang', 'Den', 'Xanh navy', 'Xam', 'Be', 'Xanh la', 'Do'],
        'price_range': (150000, 800000),
        'name_template': '{type} Nam {brand} {material} Mau {color}',
        'desc_template': '{type} nam chat lieu {material} cao cap, form {form}, thoang mat, de phoi do.'
    },
    'cat_pants_men': {
        'brands': ['Coolmate', 'Uniqlo', 'Levis', 'Zara', 'Local Brand', 'Aristino'],
        'types': ['Quan jean', 'Quan kaki', 'Quan short', 'Quan jogger', 'Quan tay'],
        'fits': ['Slim fit', 'Regular fit', 'Relaxed fit', 'Skinny'],
        'colors': ['Xanh dam', 'Den', 'Xam', 'Be', 'Nau'],
        'price_range': (200000, 1200000),
        'name_template': '{type} Nam {brand} {fit} Mau {color}',
        'desc_template': '{type} nam {brand}, {fit}, chat lieu cao cap, co gian nhe, thoai mai van dong.'
    },
    'cat_shoes_men': {
        'brands': ['Nike', 'Adidas', 'Puma', 'New Balance', 'Converse', 'Vans', 'Biti\'s'],
        'types': ['Giay sneaker', 'Giay the thao', 'Giay chay bo', 'Giay da banh'],
        'models': ['Air Force 1', 'Air Max', 'Jordan', 'Stan Smith', 'Superstar', 'RS-X', '574', 'Chuck Taylor', 'Old Skool', 'Hunter'],
        'colors': ['Trang', 'Den', 'Trang Den', 'Do', 'Xanh'],
        'price_range': (500000, 5000000),
        'name_template': '{brand} {model} {color}',
        'desc_template': 'Giay {brand} {model} chinh hang, de cao su ben, thoang khi, phu hop {activity}.'
    },
    'cat_dress': {
        'brands': ['Zara', 'H&M', 'Mango', 'IVY Moda', 'Elise', 'Marc Fashion'],
        'types': ['Dam maxi', 'Dam body', 'Dam xoe', 'Vay midi', 'Dam so mi', 'Dam du tiec'],
        'styles': ['Hoa nhi', 'Tron', 'Caro', 'Ke soc', 'Ren'],
        'colors': ['Den', 'Trang', 'Do', 'Xanh', 'Hong', 'Vang'],
        'price_range': (250000, 1500000),
        'name_template': '{type} Nu {brand} {style} Mau {color}',
        'desc_template': '{type} nu {brand} hoa tiet {style}, chat lieu mem mai, ton dang, phu hop {occasion}.'
    },
    'cat_tops_women': {
        'brands': ['Zara', 'H&M', 'Uniqlo', 'IVY Moda', 'Elise', 'Marc Fashion'],
        'types': ['Ao thun', 'Ao so mi', 'Ao croptop', 'Ao khoac', 'Cardigan', 'Blouse'],
        'styles': ['Basic', 'Tay phong', 'Tay dai', 'Hai day', 'Lech vai'],
        'colors': ['Trang', 'Den', 'Hong', 'Be', 'Xanh mint'],
        'price_range': (150000, 700000),
        'name_template': '{type} Nu {brand} {style} Mau {color}',
        'desc_template': '{type} nu {brand} kieu {style}, chat lieu thoang mat, de phoi do.'
    },
    'cat_lipstick': {
        'brands': ['MAC', 'Maybelline', '3CE', 'Romand', 'Black Rouge', 'Merzy', 'Espoir'],
        'types': ['Son thoi', 'Son kem', 'Son li', 'Lip tint', 'Son duong'],
        'colors': ['Do', 'Hong', 'Cam', 'Nude', 'Berry', 'Nau dat'],
        'finishes': ['Li', 'Bong', 'Velvet', 'Satin'],
        'price_range': (100000, 600000),
        'name_template': '{brand} {type} {finish} Mau {color}',
        'desc_template': 'Son {brand} {type} {finish}, mau {color} len moi chuan, ben mau, khong kho moi.'
    },
    'cat_skincare': {
        'brands': ['Innisfree', 'The Face Shop', 'Laneige', 'Senka', 'Cetaphil', 'La Roche-Posay', 'Some By Mi'],
        'types': ['Sua rua mat', 'Toner', 'Serum', 'Kem duong', 'Kem chong nang', 'Mat na'],
        'benefits': ['Duong am', 'Tri mun', 'Chong lao hoa', 'Lam sang', 'Se khit lo chan long'],
        'price_range': (100000, 800000),
        'name_template': '{brand} {type} {benefit}',
        'desc_template': '{type} {brand} cong dung {benefit}, phu hop da {skin_type}, khong gay kich ung.'
    },
    'cat_kitchen_appliances': {
        'brands': ['Philips', 'Panasonic', 'Sunhouse', 'Lock&Lock', 'Tefal', 'Delonghi', 'Xiaomi'],
        'types': ['Noi chien khong dau', 'May xay sinh to', 'May pha ca phe', 'Lo vi song', 'Noi com dien', 'Am sieu toc'],
        'capacities': ['2L', '4L', '6L', '1.5L', '1.8L'],
        'price_range': (500000, 8000000),
        'name_template': '{brand} {type} {capacity}',
        'desc_template': '{type} {brand} dung tich {capacity}, cong suat lon, tiet kiem dien, bao hanh {warranty} nam.'
    },
    'cat_headphones': {
        'brands': ['Sony', 'JBL', 'Bose', 'Apple', 'Samsung', 'Anker', 'Xiaomi'],
        'types': ['Tai nghe chup tai', 'Tai nghe true wireless', 'Tai nghe in-ear', 'Tai nghe gaming'],
        'features': ['Chong on ANC', 'Bluetooth 5.3', 'Pin 30h', 'Mic khong day'],
        'price_range': (300000, 10000000),
        'name_template': '{brand} {type} {feature}',
        'desc_template': 'Tai nghe {brand} {type}, {feature}, am thanh Hi-Res, phu hop {use_case}.'
    }
}

# Additional context for descriptions
USE_CASES = ['lam viec van phong', 'hoc tap', 'choi game', 'do hoa', 'lap trinh']
FEATURES = ['5G', 'chong nuoc IP68', 'sac khong day', 'man hinh 120Hz']
FORMS = ['slim fit', 'regular', 'oversize']
ACTIVITIES = ['di bo', 'chay bo', 'tap gym', 'di choi']
OCCASIONS = ['di lam', 'di choi', 'du tiec', 'hen ho']
SKIN_TYPES = ['dau', 'kho', 'hon hop', 'nhay cam']
WARRANTIES = ['1', '2', '3']


def generate_product(category_id: str, template: dict, index: int) -> dict:
    """Generate a single synthetic product"""

    # Random selections
    brand = random.choice(template['brands'])

    # Generate model name with random number
    if 'models' in template:
        model = random.choice(template['models']).format(n=random.randint(10, 99))
    else:
        model = ''

    # Build name from template
    name_parts = {
        'brand': brand,
        'model': model,
        'type': random.choice(template.get('types', [''])),
        'spec': random.choice(template.get('specs', [''])),
        'ram': random.choice(template.get('ram', [''])),
        'storage': random.choice(template.get('storage', [''])),
        'material': random.choice(template.get('materials', [''])),
        'color': random.choice(template.get('colors', [''])),
        'fit': random.choice(template.get('fits', [''])),
        'style': random.choice(template.get('styles', [''])),
        'finish': random.choice(template.get('finishes', [''])),
        'benefit': random.choice(template.get('benefits', [''])),
        'capacity': random.choice(template.get('capacities', [''])),
        'feature': random.choice(template.get('features', ['']))
    }

    name = template['name_template'].format(**name_parts).strip()
    name = ' '.join(name.split())  # Clean up extra spaces

    # Generate description
    desc_parts = {
        **name_parts,
        'use_case': random.choice(USE_CASES),
        'feature': random.choice(FEATURES),
        'form': random.choice(FORMS),
        'activity': random.choice(ACTIVITIES),
        'occasion': random.choice(OCCASIONS),
        'skin_type': random.choice(SKIN_TYPES),
        'warranty': random.choice(WARRANTIES)
    }
    description = template['desc_template'].format(**desc_parts)

    # Generate price
    min_price, max_price = template['price_range']
    price = random.randint(min_price // 10000, max_price // 10000) * 10000

    # Random discount (30% chance)
    compare_price = None
    if random.random() < 0.3:
        compare_price = int(price * random.uniform(1.1, 1.4) // 10000) * 10000

    # Generate slug
    slug = name.lower()
    for vn_char, en_char in [('a', 'a'), ('e', 'e'), ('i', 'i'), ('o', 'o'), ('u', 'u'),
                              ('d', 'd'), (' ', '-'), ("'", ''), ('"', '')]:
        slug = slug.replace(vn_char, en_char)
    import re
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    slug = f"{slug}-{index}"[:100]

    # Random stats
    rating = round(random.uniform(3.5, 5.0), 1)
    review_count = random.randint(0, 500)
    sold_count = random.randint(0, 1000)
    is_featured = rating >= 4.5 and sold_count >= 100

    return {
        'id': str(uuid.uuid4()),
        'name': name,
        'slug': slug,
        'sku': f"SYN-{category_id[-6:].upper()}-{index:04d}",
        'price': price,
        'compare_price': compare_price,
        'brand': brand,
        'description': description,
        'short_description': description[:150] + '...' if len(description) > 150 else description,
        'stock_quantity': random.randint(10, 200),
        'is_featured': is_featured,
        'status': 'active',
        'category_id': category_id,
        'category_name_vi': '',  # Will be filled from mapping
        'category_name_en': '',
        'category_slug': '',
        'category_level': 2,
        'source': 'synthetic',
        'source_id': f'syn-{index}',
        'source_url': '',
        'image_url': None,
        'rating_avg': rating,
        'rating_count': review_count,
        'sold_count': sold_count,
        'dataset_tag': 'synthetic_large',
        'normalized_at': datetime.now().isoformat()
    }


def load_category_mapping(filepath: str) -> dict:
    """Load category mapping for name lookups"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    mapping = {}

    def flatten(categories):
        for cat in categories:
            mapping[cat['id']] = {
                'name_vi': cat['name_vi'],
                'name_en': cat['name_en'],
                'slug': cat['slug'],
                'level': cat['level']
            }
            if cat.get('children'):
                flatten(cat['children'])

    flatten(data['categories'])
    return mapping


def generate_dataset(count: int, category_mapping: dict) -> List[dict]:
    """Generate full synthetic dataset"""
    products = []

    # Distribute products across categories
    categories = list(PRODUCT_TEMPLATES.keys())
    per_category = count // len(categories)
    remainder = count % len(categories)

    index = 0
    for cat_id in categories:
        template = PRODUCT_TEMPLATES[cat_id]
        cat_count = per_category + (1 if remainder > 0 else 0)
        remainder -= 1

        for _ in range(cat_count):
            product = generate_product(cat_id, template, index)

            # Fill category info from mapping
            if cat_id in category_mapping:
                cat_info = category_mapping[cat_id]
                product['category_name_vi'] = cat_info['name_vi']
                product['category_name_en'] = cat_info['name_en']
                product['category_slug'] = cat_info['slug']
                product['category_level'] = cat_info['level']

            products.append(product)
            index += 1

    random.shuffle(products)
    return products


def main():
    parser = argparse.ArgumentParser(description='Generate synthetic large dataset')
    parser.add_argument('--output', '-o', default='data/processed/synthetic_large.json',
                        help='Output JSON file')
    parser.add_argument('--count', '-n', type=int, default=500,
                        help='Number of products to generate')
    parser.add_argument('--category-map', '-c', default='scripts/data/category_mapping.json',
                        help='Category mapping file')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility')

    args = parser.parse_args()

    random.seed(args.seed)

    # Load category mapping
    category_mapping = {}
    if os.path.exists(args.category_map):
        category_mapping = load_category_mapping(args.category_map)
        print(f"Loaded {len(category_mapping)} categories from mapping")

    # Generate products
    print(f"Generating {args.count} synthetic products...")
    products = generate_dataset(args.count, category_mapping)

    # Save
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    data = {
        'dataset': 'synthetic_large',
        'generated_at': datetime.now().isoformat(),
        'total_count': len(products),
        'seed': args.seed,
        'products': products
    }

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nGenerated {len(products)} products")
    print(f"Saved to: {args.output}")

    # Category breakdown
    cat_counts = {}
    for p in products:
        cat = p['category_name_en'] or p['category_id']
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    print("\nBy category:")
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")


if __name__ == '__main__':
    main()
