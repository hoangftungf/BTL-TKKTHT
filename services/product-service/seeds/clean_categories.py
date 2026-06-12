import os
import sys
import re
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'product_project.settings')
django.setup()

from product_app.models import Category, Product

def slugify_vietnamese(text):
    text = text.lower()
    unicode_map = {
        'a': 'áàảãạăắằẳẵặâấầẩẫậ',
        'd': 'đ',
        'e': 'éèẻẽẹêếềểễệ',
        'i': 'íìỉĩị',
        'o': 'óòỏõọôốồổỗộơớờởỡợ',
        'u': 'úùủũụưứừửữự',
        'y': 'ýỳỷỹỵ'
    }
    for char, replacements in unicode_map.items():
        for rep in replacements:
            text = text.replace(rep, char)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

CLEAN_TREE = {
    'Điện thoại & Thiết bị số': {
        'slug': 'dien-thoai-thiet-bi-so',
        'children': {
            'Điện thoại Smartphone': ['Smartphone', 'Dien thoai & Phu kien', 'Phones & Tablets'],
            'Máy tính bảng': ['Tablet'],
            'Phụ kiện điện thoại': ['Phu kien dien thoai', 'Phone Accessories']
        }
    },
    'Máy tính & Laptop': {
        'slug': 'may-tinh-laptop',
        'children': {
            'Laptop': ['Laptop'],
            'PC & Máy tính để bàn': ['PC & May tinh de ban', 'Desktop PC', 'Computers'],
            'Linh kiện máy tính': ['Linh kien may tinh', 'Components']
        }
    },
    'Thời trang': {
        'slug': 'thoi-trang',
        'children': {
            'Thời trang Nam': {
                'slug': 'thoi-trang-nam',
                'children': {
                    'Áo nam': ['Áo nam', 'Ao nam', 'Shirt'],
                    'Quần nam': ['Quan nam', 'Pants'],
                    'Giày nam': ['Giay nam', 'Giày nam', 'Shoes']
                }
            },
            'Thời trang Nữ': {
                'slug': 'thoi-trang-nu',
                'children': {
                    'Đầm & Váy': ['Dam/Vay', 'Dress', 'Heels', 'Tops'],
                    'Áo nữ': ['Ao nu'],
                    'Giày nữ': ['Giay nu']
                }
            }
        }
    },
    'Đồ gia dụng & Nhà bếp': {
        'slug': 'do-gia-dung-nha-bep',
        'children': {
            'Đồ dùng nhà bếp': ['Do dung nha bep', 'Cookware', 'Kitchen Appliances', 'Home & Kitchen'],
            'Đồ dùng phòng ngủ': ['Do dung phong ngu', 'Furniture'],
            'Đồ dùng phòng tắm': ['Do dung phong tam'],
            'Thiết bị điện gia dụng': ['Refrigerator', 'Washing Machine', 'Air Conditioner', 'Electronics']
        }
    },
    'Sách & Thiết bị học tập': {
        'slug': 'sach-thiet-bi-hoc-tap',
        'children': {
            'Sách ngoại văn': ['Books', 'Books & Office'],
            'Văn phòng phẩm': ['Stationery']
        }
    },
    'Mỹ phẩm & Chăm sóc cá nhân': {
        'slug': 'my-pham-cham-soc-ca-nhan',
        'children': {
            'Trang điểm': ['Lipstick', 'Foundation', 'Beauty & Cosmetics'],
            'Chăm sóc da': ['Skincare']
        }
    },
    'Thể thao & Dã ngoại': {
        'slug': 'the-thao-da-ngoai',
        'children': {
            'Dụng cụ thể thao': ['Gym Equipment', 'Sports & Outdoor'],
            'Đồ dã ngoại': ['Outdoor Gear']
        }
    },
    'Phụ kiện & Trang sức': {
        'slug': 'phu-kien-trang-suc',
        'children': {
            'Đồng hồ': ['Watches', 'Accessories'],
            'Túi xách': ['Bags']
        }
    }
}

def get_or_create_cat(name, slug, parent=None, display_order=0):
    cat, created = Category.objects.get_or_create(
        slug=slug,
        defaults={
            'name': name,
            'parent': parent,
            'display_order': display_order,
            'is_active': True
        }
    )
    if not created:
        updated = False
        if cat.name != name:
            cat.name = name
            updated = True
        if cat.parent != parent:
            cat.parent = parent
            updated = True
        if cat.display_order != display_order:
            cat.display_order = display_order
            updated = True
        if updated:
            cat.save()
    return cat

def map_old_categories(target_cat, source_names):
    for name in source_names:
        old_cats = Category.objects.filter(name__iexact=name)
        for old_cat in old_cats:
            if old_cat.id == target_cat.id:
                continue
            products_count = Product.objects.filter(category=old_cat).update(category=target_cat)
            if products_count > 0:
                print(f"    [Merge] Mapped {products_count} products from '{old_cat.name}' (ID: {old_cat.id}) to '{target_cat.name}'")

def run_cleansing():
    print("=" * 60)
    print("  PRODUCT CATEGORY DATA CLEANSING SCRIPT")
    print("=" * 60)

    clean_category_ids = set()

    for idx, (root_name, root_data) in enumerate(CLEAN_TREE.items()):
        # 1. Create/Update Root Category
        root_cat = get_or_create_cat(root_name, root_data['slug'], parent=None, display_order=idx)
        print(f"\n[Root] {root_cat.name} (Slug: {root_cat.slug})")
        clean_category_ids.add(root_cat.id)

        # 2. Process Children
        for child_idx, (child_name, child_val) in enumerate(root_data['children'].items()):
            if isinstance(child_val, dict):
                # Has sub-children (e.g. Thời trang Nam)
                child_cat = get_or_create_cat(child_name, child_val['slug'], parent=root_cat, display_order=child_idx)
                print(f"  ├── [Sub-Parent] {child_cat.name}")
                clean_category_ids.add(child_cat.id)

                for sub_idx, (sub_name, source_list) in enumerate(child_val['children'].items()):
                    sub_cat = get_or_create_cat(sub_name, slugify_vietnamese(sub_name), parent=child_cat, display_order=sub_idx)
                    print(f"  │    └── [Leaf] {sub_cat.name}")
                    clean_category_ids.add(sub_cat.id)
                    map_old_categories(sub_cat, source_list)
                    # Also map products carrying the leaf name itself
                    map_old_categories(sub_cat, [sub_name])
            else:
                # Direct leaf category (e.g. Điện thoại Smartphone)
                child_cat = get_or_create_cat(child_name, slugify_vietnamese(child_name), parent=root_cat, display_order=child_idx)
                print(f"  └── [Leaf] {child_cat.name}")
                clean_category_ids.add(child_cat.id)
                map_old_categories(child_cat, child_val)
                # Also map products carrying the leaf name itself
                map_old_categories(child_cat, [child_name])

    # 3. Clean up orphaned products
    # Find any products linked to categories that are about to be deleted and map them to a fallback category
    # (Just in case some categories didn't match the iexact search, map them to root categories)
    # Let's find categories that are NOT in clean_category_ids
    old_categories = Category.objects.exclude(id__in=clean_category_ids)
    print("\n" + "=" * 60)
    print(f"Cleaning up {old_categories.count()} obsolete categories...")
    print("=" * 60)

    # Let's see if any old categories still have products, map them to a root fallback
    fallback_cat = Category.objects.filter(slug='do-gia-dung-nha-bep').first()
    for old_cat in old_categories:
        prods = Product.objects.filter(category=old_cat)
        if prods.exists():
            # Try to match name to a clean category or fallback
            target = None
            for idx, clean_id in enumerate(clean_category_ids):
                clean_cat = Category.objects.get(id=clean_id)
                if clean_cat.name.lower() in old_cat.name.lower() or old_cat.name.lower() in clean_cat.name.lower():
                    target = clean_cat
                    break
            if not target:
                target = fallback_cat
            
            if target:
                prods_count = prods.update(category=target)
                print(f"  Mapped {prods_count} orphaned products from obsolete '{old_cat.name}' to '{target.name}'")

    # 4. Safely delete obsolete categories
    deleted_count, _ = old_categories.delete()
    print(f"\nDeleted {deleted_count} obsolete/duplicate category records.")
    print("=" * 60)
    print("  DATA CLEANSING COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == '__main__':
    run_cleansing()
