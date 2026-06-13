#!/usr/bin/env python
"""
Export Knowledge Graph Data to CSV files.

Generates 13 CSV files for Neo4j knowledge graph import:
  Nodes:    products, categories, brands, users, colors, materials
  Edges:    belongs_to, made_by, has_color, has_material,
            user_interactions, co_purchased, user_similarity

Usage:
    python scripts/export_kg_csv.py
    python scripts/export_kg_csv.py --output data/kg_csv
"""

import csv
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / 'data' / 'kg_csv'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Color & Material dictionaries from rebuild_graph_schema.py ──────────────
COLORS = {
    'Đen': ['mau den', 'màu đen', 'đen', 'black', 'den'],
    'Trắng': ['mau trang', 'màu trắng', 'trắng', 'white', 'trang'],
    'Hồng': ['mau hong', 'màu hồng', 'hồng', 'pink', 'hong'],
    'Đỏ': ['mau do', 'màu đỏ', 'đỏ', 'red', 'do'],
    'Xanh': ['mau xanh', 'màu xanh', 'xanh', 'blue', 'green'],
    'Vàng': ['mau vang', 'màu vàng', 'vàng', 'yellow', 'vang'],
    'Nâu': ['mau nau', 'màu nâu', 'nâu', 'brown', 'nau'],
    'Xám': ['mau xam', 'màu xám', 'xám', 'grey', 'gray', 'xam'],
    'Cam': ['mau cam', 'màu cam', 'cam', 'orange'],
    'Tím': ['mau tim', 'màu tím', 'tím', 'purple', 'tim'],
}

MATERIALS = {
    'Jean': ['jean', 'bò', 'denim', 'bo'],
    'Cotton': ['cotton', 'thun'],
    'Lụa': ['lụa', 'silk', 'lua'],
    'Da': [' da ', 'da bò', 'da thật', 'leather'],
    'Len': ['len', 'wool'],
    'Polyester': ['polyester', 'poly', 'nỉ', 'spandex', 'ni'],
    'Kaki': ['kaki', 'khaki'],
    'Linen': ['linen', 'đũi', 'dui'],
}

# ── Helper functions ─────────────────────────────────────────────────────────

def extract_color(name, description=''):
    text = ((name or '') + ' ' + (description or '')).lower()
    for color, keywords in COLORS.items():
        for kw in keywords:
            # Use word-boundary match to avoid false positives (e.g. "dong" ≠ "do")
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                return color
    return None


def extract_material(name, description=''):
    text = ((name or '') + ' ' + (description or '')).lower()
    for material, keywords in MATERIALS.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text):
                return material
    return None


def write_csv(filename, headers, rows):
    path = OUTPUT_DIR / filename
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    print(f"  ✓ {filename:<35s} → {len(rows):,} rows")


# ── 1. Load all data sources ─────────────────────────────────────────────────

print("=" * 60)
print("EXPORT KNOWLEDGE GRAPH CSV FILES")
print("=" * 60)
print()

# 1a. Category mapping (bilingual, 45 categories, 3 levels)
print("Loading data sources...")
with open(BASE_DIR / 'scripts' / 'data' / 'category_mapping.json', 'r', encoding='utf-8') as f:
    cat_data = json.load(f)


def flatten_categories(nodes, parent='', level=0):
    """Recursively flatten category tree → list of dicts."""
    result = []
    for cat in nodes:
        cat_id = cat['id']
        result.append({
            'id': cat_id,
            'name_vi': cat['name_vi'],
            'name_en': cat['name_en'],
            'slug': cat['slug'],
            'level': cat.get('level', level),
            'parent_id': parent or None,
        })
        if 'children' in cat and cat['children']:
            result.extend(flatten_categories(cat['children'], cat_id, cat.get('level', level) + 1))
    return result


flat_categories = flatten_categories(cat_data['categories'])
cat_lookup = {c['name_vi'].lower(): c for c in flat_categories}  # map vi name → full info
cat_by_id = {c['id']: c for c in flat_categories}

# 1b. Synthetic large products (500 products)
with open(BASE_DIR / 'data' / 'processed' / 'synthetic_large.json', 'r', encoding='utf-8') as f:
    syn_data = json.load(f)
syn_products = syn_data.get('products', [])

# 1c. Tiki API products (137 products)
with open(BASE_DIR / 'data' / 'raw' / 'tiki_api_products.json', 'r', encoding='utf-8') as f:
    tiki_data = json.load(f)
tiki_products = tiki_data.get('products', [])

# 1d. Basic products CSV (100 products) — fallback
basic_products = []
basic_products_path = BASE_DIR / 'data' / 'products.csv'
if basic_products_path.exists():
    with open(basic_products_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        basic_products = list(reader)

# 1e. User behavior (14,861 interactions)
interactions = []
inter_path = BASE_DIR / 'scripts' / 'data_user500.csv'
if inter_path.exists():
    with open(inter_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        interactions = list(reader)

print(f"  Categories:    {len(flat_categories)} nodes (3 levels)")
print(f"  Synth products:  {len(syn_products)} products")
print(f"  Tiki products:   {len(tiki_products)} products")
print(f"  Basic products:  {len(basic_products)} products")
print(f"  User interactions: {len(interactions):,} events")
print()

# ── 2. Build unified product + category + brand datasets ─────────────────────

# Merge all products into a single unified list
all_products = []
seen_ids = set()

# Helper to standardize category names (Vietnamese, diacritics)
CATEGORY_ALIASES = {
    'dien thoai': 'Điện thoại Smartphone',
    'laptop': 'Laptop',
    'may tinh bang': 'Máy tính bảng',
    'phu kien': 'Phụ kiện điện thoại',
    'dong ho': 'Đồng hồ',
    'thoi trang': 'Thời trang',
    'gia dung': 'Gia dụng',
    'sach': 'Sách',
    'the thao': 'Thể thao',
    'my pham': 'Mỹ phẩm',
    'dien tu - cong nghe': 'Điện tử - Công nghệ',
    'dien tu': 'Điện tử - Công nghệ',
    'cong nghe': 'Điện tử - Công nghệ',
}

# Track all unique categories and brands
all_categories = {}   # name_vi → {id, name_vi, name_en, slug, level}
all_brands = set()
product_nodes = []

# Process synthetic_large products (richest data)
for p in syn_products:
    pid = p['id']
    if pid in seen_ids:
        continue
    seen_ids.add(pid)

    cat_name = p.get('category_name_vi', '') or p.get('category_name_en', '')
    brand = (p.get('brand') or '').strip()

    # Map category
    cat_info = cat_by_id.get(p.get('category_id'))
    if not cat_info and cat_name:
        cat_info = cat_lookup.get(cat_name.lower())

    product_nodes.append({
        'product_id': pid,
        'name': p['name'],
        'slug': p.get('slug', ''),
        'price': p.get('price', 0),
        'compare_price': p.get('compare_price') or '',
        'brand': brand,
        'category_id': cat_info['id'] if cat_info else (p.get('category_id') or ''),
        'category_name': cat_info['name_vi'] if cat_info else cat_name,
        'description': p.get('description', '') or '',
        'short_description': p.get('short_description', '') or '',
        'stock_quantity': p.get('stock_quantity', 0),
        'rating_avg': round(p.get('rating_avg', 0) or 0, 1),
        'rating_count': p.get('rating_count', 0) or 0,
        'sold_count': p.get('sold_count', 0) or 0,
        'status': p.get('status', 'active'),
        'source': 'synthetic_large',
    })

    if cat_info:
        all_categories[cat_info['name_vi']] = cat_info
    if brand:
        all_brands.add(brand)

# Process Tiki products
for p in tiki_products:
    source_id = f"tiki_{p.get('source_id', '')}"
    if source_id in seen_ids:
        continue
    seen_ids.add(source_id)

    cat_source = (p.get('category_source', '') or '').strip()
    brand = (p.get('brand', '') or '').strip()

    # Try to map Tiki category → our category system
    mapped_cat = None
    cat_lower = cat_source.lower()
    if cat_lower in CATEGORY_ALIASES:
        mapped_name = CATEGORY_ALIASES[cat_lower]
        mapped_cat = cat_lookup.get(mapped_name.lower())
    if not mapped_cat:
        mapped_cat = cat_lookup.get(cat_lower)

    product_nodes.append({
        'product_id': source_id,
        'name': p.get('name', ''),
        'slug': '',
        'price': p.get('price', 0),
        'compare_price': p.get('original_price', '') or '',
        'brand': brand,
        'category_id': mapped_cat['id'] if mapped_cat else '',
        'category_name': mapped_cat['name_vi'] if mapped_cat else cat_source,
        'description': '',
        'short_description': '',
        'stock_quantity': 0,
        'rating_avg': round(p.get('rating', 0) or 0, 1),
        'rating_count': 0,
        'sold_count': p.get('sold', 0) or 0,
        'status': 'active',
        'source': 'tiki',
    })

    if mapped_cat:
        all_categories[mapped_cat['name_vi']] = mapped_cat
    if brand:
        all_brands.add(brand)

# Process basic products (fallback if not already covered)
for p in basic_products:
    pid = p.get('product_id', '')
    if pid in seen_ids:
        continue
    seen_ids.add(pid)

    cat_name = (p.get('category', '') or '').strip()
    brand = (p.get('brand', '') or '').strip()

    # Map simple categories
    mapped_cat = None
    cat_lower = cat_name.lower()
    if cat_lower in CATEGORY_ALIASES:
        mapped_name = CATEGORY_ALIASES[cat_lower]
        mapped_cat = cat_lookup.get(mapped_name.lower())
    if not mapped_cat:
        mapped_cat = cat_lookup.get(cat_lower)

    product_nodes.append({
        'product_id': pid,
        'name': p.get('name', ''),
        'slug': '',
        'price': int(float(p.get('price', 0))),
        'compare_price': '',
        'brand': brand,
        'category_id': mapped_cat['id'] if mapped_cat else '',
        'category_name': mapped_cat['name_vi'] if mapped_cat else cat_name,
        'description': '',
        'short_description': '',
        'stock_quantity': 0,
        'rating_avg': 0,
        'rating_count': 0,
        'sold_count': 0,
        'status': 'active',
        'source': 'basic_csv',
    })

    if mapped_cat:
        all_categories[mapped_cat['name_vi']] = mapped_cat
    if brand:
        all_brands.add(brand)

print(f"Unified products: {len(product_nodes)} total")
print(f"Unique categories: {len(all_categories)}")
print(f"Unique brands: {len(all_brands)}")
print()

# ── 3. Export NODE CSV files ─────────────────────────────────────────────────

print("Exporting NODE files...")
print("-" * 40)

# 3a. products.csv
write_csv('products.csv',
    ['product_id:ID', 'name', 'slug', 'price:float', 'compare_price:float',
     'status', 'stock_quantity:int', 'rating_avg:float', 'rating_count:int',
     'sold_count:int', 'description', 'source', ':LABEL'],
    [[p['product_id'], p['name'], p['slug'], p['price'],
      p['compare_price'] if p['compare_price'] else '', p['status'],
      p['stock_quantity'], p['rating_avg'], p['rating_count'],
      p['sold_count'], p['description'][:200], p['source'], 'Product']
     for p in product_nodes])

# 3b. categories.csv — all 40 categories from mapping (used + unused)
cat_rows = []
included_cats = set()
for cat in flat_categories:
    included_cats.add(cat['name_vi'])
    cat_rows.append([
        cat['id'], cat['name_vi'], cat.get('name_en', ''),
        cat.get('slug', ''), cat.get('level', 0),
        cat.get('parent_id') or '', 'Category'
    ])
# Also include any categories found in product data but not in mapping
for name_vi, info in sorted(all_categories.items(), key=lambda x: x[1].get('level', 0)):
    if name_vi not in included_cats:
        cat_rows.append([
            info['id'], info['name_vi'], info.get('name_en', ''),
            info.get('slug', ''), info.get('level', 0),
            info.get('parent_id') or '', 'Category'
        ])
write_csv('categories.csv',
    ['category_id:ID', 'name_vi', 'name_en', 'slug', 'level:int',
     'parent_id', ':LABEL'],
    cat_rows)

# 3c. brands.csv
brand_rows = sorted([[b, 'Brand'] for b in all_brands])
write_csv('brands.csv', ['name:ID', ':LABEL'], brand_rows)

# 3d. users.csv
user_ids = set()
for row in interactions:
    user_ids.add(row['user_id'])

# Map users to preferred categories based on their purchase history
user_prefs = defaultdict(lambda: defaultdict(int))
for row in interactions:
    uid = row['user_id']
    pid = row['product_id']
    action = row['action']
    weight = {'purchase': 5, 'add_to_cart': 3, 'wishlist': 2, 'view': 1, 'click': 1}
    w = weight.get(action, 0)
    user_prefs[uid][pid] += w

user_rows = []
for uid in sorted(user_ids):
    user_rows.append([uid, uid, 'User'])
write_csv('users.csv', ['user_id:ID', 'name', ':LABEL'], user_rows)

# 3e. colors.csv
color_rows = [[color, 'Color'] for color in COLORS.keys()]
write_csv('colors.csv', ['name:ID', ':LABEL'], color_rows)

# 3f. materials.csv
material_rows = [[mat, 'Material'] for mat in MATERIALS.keys()]
write_csv('materials.csv', ['name:ID', ':LABEL'], material_rows)

# ── 4. Export RELATIONSHIP CSV files ─────────────────────────────────────────

print()
print("Exporting RELATIONSHIP files...")
print("-" * 40)

# 4a. belongs_to.csv — Product → Category
bt_rows = []
for p in product_nodes:
    if p['category_id']:
        bt_rows.append([p['product_id'], p['category_id']])
write_csv('belongs_to.csv',
    [':START_ID(Product)', ':END_ID(Category)'], bt_rows)

# 4b. made_by.csv — Product → Brand
mb_rows = []
for p in product_nodes:
    if p['brand']:
        mb_rows.append([p['product_id'], p['brand']])
write_csv('made_by.csv',
    [':START_ID(Product)', ':END_ID(Brand)'], mb_rows)

# 4c. has_color.csv — Product → Color (extracted via keywords)
hc_rows = []
for p in product_nodes:
    color = extract_color(p['name'], p['description'])
    if color:
        hc_rows.append([p['product_id'], color])
write_csv('has_color.csv',
    [':START_ID(Product)', ':END_ID(Color)'], hc_rows)

# 4d. has_material.csv — Product → Material (extracted via keywords)
hm_rows = []
for p in product_nodes:
    material = extract_material(p['name'], p['description'])
    if material:
        hm_rows.append([p['product_id'], material])
write_csv('has_material.csv',
    [':START_ID(Product)', ':END_ID(Material)'], hm_rows)

# 4e. user_interactions.csv — aggregated User → Product interactions
print("  Aggregating user interactions...")
# Aggregate: (user_id, product_id, action) → count, last_time, total_duration
agg_interactions = defaultdict(lambda: {'count': 0, 'last_time': '', 'total_duration': 0})
for row in interactions:
    key = (row['user_id'], row['product_id'], row['action'])
    agg = agg_interactions[key]
    agg['count'] += 1
    ts = row['timestamp']
    if ts > agg['last_time']:
        agg['last_time'] = ts
    agg['total_duration'] += int(row.get('duration', 0) or 0)

ui_rows = []
for (uid, pid, action), agg in agg_interactions.items():
    ui_rows.append([
        uid, pid, action, agg['count'],
        agg['last_time'], agg['total_duration']
    ])
write_csv('user_interactions.csv',
    [':START_ID(User)', ':END_ID(Product)', 'action_type', 'count:int',
     'last_time:datetime', 'total_duration:int'],
    ui_rows)

# 4f. co_purchased.csv — Product ↔ Product (co-purchase similarity)
print("  Computing co-purchase similarity...")
user_products = defaultdict(set)
for row in interactions:
    if row['action'] == 'purchase':
        user_products[row['user_id']].add(row['product_id'])

# Count co-purchases between every pair of products
co_purchase_counts = defaultdict(int)
product_set = set()
for uid, prods in user_products.items():
    product_set.update(prods)
    prod_list = sorted(prods)
    for i in range(len(prod_list)):
        for j in range(i + 1, len(prod_list)):
            pair = (prod_list[i], prod_list[j])
            co_purchase_counts[pair] += 1

cp_rows = []
for (p1, p2), count in co_purchase_counts.items():
    if count >= 2:  # minimum 2 common purchasers
        cp_rows.append([p1, p2, count])
write_csv('co_purchased.csv',
    [':START_ID(Product)', ':END_ID(Product)', 'score:int'], cp_rows)

# 4g. user_similarity.csv — User ↔ User (common purchased/viewed products)
print("  Computing user similarity...")
user_product_set = {}
for uid, prods in user_products.items():
    user_product_set[uid] = prods

user_ids_list = sorted(user_product_set.keys())
us_rows = []
for i in range(len(user_ids_list)):
    for j in range(i + 1, len(user_ids_list)):
        u1, u2 = user_ids_list[i], user_ids_list[j]
        common = len(user_product_set[u1] & user_product_set[u2])
        if common >= 2:
            us_rows.append([u1, u2, common])

write_csv('user_similarity.csv',
    [':START_ID(User)', ':END_ID(User)', 'score:int'], us_rows)

# ── 5. Summary ───────────────────────────────────────────────────────────────

print()
print("=" * 60)
print("EXPORT COMPLETE")
print("=" * 60)
print(f"Output directory: {OUTPUT_DIR}")
print()
print("Files generated:")
for f in sorted(OUTPUT_DIR.iterdir()):
    if f.suffix == '.csv':
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name:<35s} {size_kb:>8.1f} KB")
print()
print("Neo4j import usage (neo4j-admin):")
print(f"  neo4j-admin database import full \\")
print(f"    --nodes={OUTPUT_DIR}/products.csv \\")
print(f"    --nodes={OUTPUT_DIR}/categories.csv \\")
print(f"    --nodes={OUTPUT_DIR}/brands.csv \\")
print(f"    --nodes={OUTPUT_DIR}/users.csv \\")
print(f"    --nodes={OUTPUT_DIR}/colors.csv \\")
print(f"    --nodes={OUTPUT_DIR}/materials.csv \\")
print(f"    --relationships={OUTPUT_DIR}/belongs_to.csv \\")
print(f"    --relationships={OUTPUT_DIR}/made_by.csv \\")
print(f"    --relationships={OUTPUT_DIR}/has_color.csv \\")
print(f"    --relationships={OUTPUT_DIR}/has_material.csv \\")
print(f"    --relationships={OUTPUT_DIR}/user_interactions.csv \\")
print(f"    --relationships={OUTPUT_DIR}/co_purchased.csv \\")
print(f"    --relationships={OUTPUT_DIR}/user_similarity.csv")
