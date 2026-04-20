"""
Seed Data Script cho Product Service
Tao du lieu mau: Categories va Products
"""
import os
import sys
import django
import uuid
from decimal import Decimal
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'product_project.settings')
django.setup()

from product_app.models import Category, Product, ProductVariant

# ============================================
# CATEGORIES DATA
# ============================================
CATEGORIES = [
    {
        'name': 'Điện thoại & Phụ kiện',
        'slug': 'dien-thoai-phu-kien',
        'description': 'Điện thoại thông minh, máy tính bảng và phụ kiện',
        'children': [
            {'name': 'Điện thoại Smartphone', 'slug': 'smartphone'},
            {'name': 'Máy tính bảng', 'slug': 'tablet'},
            {'name': 'Phụ kiện điện thoại', 'slug': 'phu-kien-dien-thoai'},
        ]
    },
    {
        'name': 'Laptop & Máy tính',
        'slug': 'laptop-may-tinh',
        'description': 'Laptop, PC và linh kiện máy tính',
        'children': [
            {'name': 'Laptop', 'slug': 'laptop'},
            {'name': 'PC & Máy tính để bàn', 'slug': 'pc-desktop'},
            {'name': 'Linh kiện máy tính', 'slug': 'linh-kien'},
        ]
    },
    {
        'name': 'Thời trang Nam',
        'slug': 'thoi-trang-nam',
        'description': 'Quần áo, giày dép thời trang nam',
        'children': [
            {'name': 'Áo nam', 'slug': 'ao-nam'},
            {'name': 'Quần nam', 'slug': 'quan-nam'},
            {'name': 'Giày nam', 'slug': 'giay-nam'},
        ]
    },
    {
        'name': 'Thời trang Nữ',
        'slug': 'thoi-trang-nu',
        'description': 'Quần áo, giày dép thời trang nữ',
        'children': [
            {'name': 'Đầm/Váy', 'slug': 'dam-vay'},
            {'name': 'Áo nữ', 'slug': 'ao-nu'},
            {'name': 'Giày nữ', 'slug': 'giay-nu'},
        ]
    },
    {
        'name': 'Đồ gia dụng',
        'slug': 'do-gia-dung',
        'description': 'Đồ dùng gia đình, nhà bếp',
        'children': [
            {'name': 'Đồ dùng nhà bếp', 'slug': 'do-dung-nha-bep'},
            {'name': 'Đồ dùng phòng ngủ', 'slug': 'do-dung-phong-ngu'},
            {'name': 'Đồ dùng phòng tắm', 'slug': 'do-dung-phong-tam'},
        ]
    },
]

# ============================================
# PRODUCTS DATA
# ============================================
PRODUCTS = {
    'smartphone': [
        {
            'name': 'iPhone 15 Pro Max 256GB',
            'slug': 'iphone-15-pro-max-256gb',
            'sku': 'IP15PM-256',
            'price': 34990000,
            'compare_price': 36990000,
            'brand': 'Apple',
            'description': 'iPhone 15 Pro Max với chip A17 Pro, camera 48MP, màn hình Super Retina XDR 6.7 inch',
            'short_description': 'iPhone 15 Pro Max - Flagship mới nhất của Apple',
            'stock_quantity': 50,
            'is_featured': True,
        },
        {
            'name': 'Samsung Galaxy S24 Ultra 512GB',
            'slug': 'samsung-galaxy-s24-ultra-512gb',
            'sku': 'SS-S24U-512',
            'price': 33990000,
            'compare_price': 35990000,
            'brand': 'Samsung',
            'description': 'Samsung Galaxy S24 Ultra với Galaxy AI, S Pen, camera 200MP',
            'short_description': 'Galaxy S24 Ultra - AI Phone đỉnh cao',
            'stock_quantity': 45,
            'is_featured': True,
        },
        {
            'name': 'Xiaomi 14 Ultra 512GB',
            'slug': 'xiaomi-14-ultra-512gb',
            'sku': 'XM-14U-512',
            'price': 23990000,
            'compare_price': 25990000,
            'brand': 'Xiaomi',
            'description': 'Xiaomi 14 Ultra với camera Leica, Snapdragon 8 Gen 3',
            'short_description': 'Xiaomi 14 Ultra - Camera phone hàng đầu',
            'stock_quantity': 30,
            'is_featured': False,
        },
        {
            'name': 'OPPO Find X7 Ultra',
            'slug': 'oppo-find-x7-ultra',
            'sku': 'OPPO-FX7U',
            'price': 22990000,
            'compare_price': None,
            'brand': 'OPPO',
            'description': 'OPPO Find X7 Ultra với camera Hasselblad, màn hình 2K AMOLED',
            'short_description': 'OPPO Find X7 Ultra - Flagship OPPO',
            'stock_quantity': 25,
            'is_featured': False,
        },
        {
            'name': 'Google Pixel 8 Pro 256GB',
            'slug': 'google-pixel-8-pro-256gb',
            'sku': 'GG-PX8P-256',
            'price': 24990000,
            'compare_price': 26990000,
            'brand': 'Google',
            'description': 'Google Pixel 8 Pro với AI tích hợp, camera Tensor G3',
            'short_description': 'Pixel 8 Pro - AI Phone của Google',
            'stock_quantity': 20,
            'is_featured': True,
        },
    ],
    'laptop': [
        {
            'name': 'MacBook Pro 14 M3 Pro 512GB',
            'slug': 'macbook-pro-14-m3-pro-512gb',
            'sku': 'MBP14-M3P-512',
            'price': 49990000,
            'compare_price': 52990000,
            'brand': 'Apple',
            'description': 'MacBook Pro 14 inch với chip M3 Pro, RAM 18GB, SSD 512GB',
            'short_description': 'MacBook Pro M3 Pro - Hiệu năng đỉnh cao',
            'stock_quantity': 20,
            'is_featured': True,
        },
        {
            'name': 'Dell XPS 15 9530 Core i7',
            'slug': 'dell-xps-15-9530-i7',
            'sku': 'DELL-XPS15-I7',
            'price': 42990000,
            'compare_price': 45990000,
            'brand': 'Dell',
            'description': 'Dell XPS 15 với Intel Core i7-13700H, RTX 4060, RAM 16GB',
            'short_description': 'Dell XPS 15 - Laptop cao cấp cho doanh nhân',
            'stock_quantity': 15,
            'is_featured': True,
        },
        {
            'name': 'ASUS ROG Strix G16 RTX 4070',
            'slug': 'asus-rog-strix-g16-rtx4070',
            'sku': 'ASUS-ROG-G16',
            'price': 38990000,
            'compare_price': 41990000,
            'brand': 'ASUS',
            'description': 'ASUS ROG Strix G16 với RTX 4070, Core i9-13980HX, 165Hz',
            'short_description': 'ROG Strix G16 - Gaming laptop mạnh mẽ',
            'stock_quantity': 25,
            'is_featured': False,
        },
        {
            'name': 'Lenovo ThinkPad X1 Carbon Gen 11',
            'slug': 'lenovo-thinkpad-x1-carbon-gen11',
            'sku': 'LEN-X1C-G11',
            'price': 35990000,
            'compare_price': None,
            'brand': 'Lenovo',
            'description': 'ThinkPad X1 Carbon với Core i7 vPro, màn hình 2.8K OLED',
            'short_description': 'ThinkPad X1 Carbon - Laptop doanh nghiệp',
            'stock_quantity': 18,
            'is_featured': False,
        },
        {
            'name': 'HP Spectre x360 14 OLED',
            'slug': 'hp-spectre-x360-14-oled',
            'sku': 'HP-SPX360-14',
            'price': 32990000,
            'compare_price': 34990000,
            'brand': 'HP',
            'description': 'HP Spectre x360 14 với màn hình OLED 2.8K, Core i7',
            'short_description': 'Spectre x360 - Laptop 2-in-1 cao cấp',
            'stock_quantity': 12,
            'is_featured': True,
        },
    ],
    'ao-nam': [
        {
            'name': 'Áo Polo Nam Cotton Premium',
            'slug': 'ao-polo-nam-cotton-premium',
            'sku': 'POLO-NAM-001',
            'price': 450000,
            'compare_price': 550000,
            'brand': 'Local Brand',
            'description': 'Áo polo nam chất liệu cotton cao cấp, form regular fit',
            'short_description': 'Áo polo cotton cao cấp cho nam',
            'stock_quantity': 100,
            'is_featured': True,
        },
        {
            'name': 'Áo Sơ Mi Nam Slim Fit Trắng',
            'slug': 'ao-so-mi-nam-slim-fit-trang',
            'sku': 'SOMI-NAM-001',
            'price': 380000,
            'compare_price': 450000,
            'brand': 'Việt Tiến',
            'description': 'Áo sơ mi nam form slim fit, chất liệu cotton pha',
            'short_description': 'Áo sơ mi trắng slim fit',
            'stock_quantity': 80,
            'is_featured': False,
        },
        {
            'name': 'Áo Thun Nam Basic Đen',
            'slug': 'ao-thun-nam-basic-den',
            'sku': 'THUN-NAM-001',
            'price': 199000,
            'compare_price': 250000,
            'brand': 'Coolmate',
            'description': 'Áo thun basic nam màu đen, chất cotton 100%',
            'short_description': 'Áo thun basic đen nam',
            'stock_quantity': 200,
            'is_featured': False,
        },
        {
            'name': 'Áo Khoác Bomber Nam',
            'slug': 'ao-khoac-bomber-nam',
            'sku': 'BOMBER-NAM-001',
            'price': 650000,
            'compare_price': 800000,
            'brand': 'MLB',
            'description': 'Áo khoác bomber nam phong cách streetwear',
            'short_description': 'Bomber jacket phong cách',
            'stock_quantity': 50,
            'is_featured': True,
        },
        {
            'name': 'Áo Hoodie Nam Oversize',
            'slug': 'ao-hoodie-nam-oversize',
            'sku': 'HOODIE-NAM-001',
            'price': 520000,
            'compare_price': 620000,
            'brand': 'Uniqlo',
            'description': 'Áo hoodie nam form oversize, có mũ, túi kangaroo',
            'short_description': 'Hoodie oversize cho nam',
            'stock_quantity': 75,
            'is_featured': False,
        },
    ],
    'dam-vay': [
        {
            'name': 'Đầm Maxi Hoa Nhí Vintage',
            'slug': 'dam-maxi-hoa-nhi-vintage',
            'sku': 'DAM-MAXI-001',
            'price': 550000,
            'compare_price': 700000,
            'brand': 'Zara',
            'description': 'Đầm maxi họa tiết hoa nhí phong cách vintage',
            'short_description': 'Đầm maxi hoa vintage',
            'stock_quantity': 60,
            'is_featured': True,
        },
        {
            'name': 'Váy Công Sở A-line Thanh Lịch',
            'slug': 'vay-cong-so-a-line',
            'sku': 'VAY-CS-001',
            'price': 480000,
            'compare_price': 580000,
            'brand': 'IVY Moda',
            'description': 'Váy công sở form A-line, phù hợp đi làm và dự tiệc',
            'short_description': 'Váy công sở thanh lịch',
            'stock_quantity': 45,
            'is_featured': False,
        },
        {
            'name': 'Đầm Body Ôm Sát Quyến Rũ',
            'slug': 'dam-body-om-sat-quyen-ru',
            'sku': 'DAM-BODY-001',
            'price': 420000,
            'compare_price': 520000,
            'brand': 'Mango',
            'description': 'Đầm body ôm sát tôn dáng, phù hợp dự tiệc',
            'short_description': 'Đầm body quyến rũ',
            'stock_quantity': 35,
            'is_featured': True,
        },
        {
            'name': 'Váy Midi Xếp Ly Hàn Quốc',
            'slug': 'vay-midi-xep-ly-han-quoc',
            'sku': 'VAY-MIDI-001',
            'price': 390000,
            'compare_price': 490000,
            'brand': 'Stylenanda',
            'description': 'Váy midi xếp ly phong cách Hàn Quốc, trẻ trung',
            'short_description': 'Váy midi Hàn Quốc',
            'stock_quantity': 55,
            'is_featured': False,
        },
        {
            'name': 'Đầm Sơ Mi Caro Basic',
            'slug': 'dam-so-mi-caro-basic',
            'sku': 'DAM-SOMI-001',
            'price': 350000,
            'compare_price': None,
            'brand': 'H&M',
            'description': 'Đầm sơ mi họa tiết caro, phong cách casual',
            'short_description': 'Đầm sơ mi caro casual',
            'stock_quantity': 70,
            'is_featured': False,
        },
    ],
    'do-dung-nha-bep': [
        {
            'name': 'Nồi chiên không dầu Philips 6.2L',
            'slug': 'noi-chien-khong-dau-philips-6l',
            'sku': 'PHILIPS-AF-6L',
            'price': 3990000,
            'compare_price': 4500000,
            'brand': 'Philips',
            'description': 'Nồi chiên không dầu Philips dung tích 6.2L, công nghệ RapidAir',
            'short_description': 'Air Fryer Philips 6.2L',
            'stock_quantity': 30,
            'is_featured': True,
        },
        {
            'name': 'Bộ nồi inox 5 chiếc Fissler',
            'slug': 'bo-noi-inox-5-chiec-fissler',
            'sku': 'FISSLER-SET5',
            'price': 8990000,
            'compare_price': 10990000,
            'brand': 'Fissler',
            'description': 'Bộ nồi inox cao cấp Fissler 5 chiếc, made in Germany',
            'short_description': 'Bộ nồi inox Đức cao cấp',
            'stock_quantity': 15,
            'is_featured': True,
        },
        {
            'name': 'Máy xay sinh tố Vitamix E320',
            'slug': 'may-xay-sinh-to-vitamix-e320',
            'sku': 'VITAMIX-E320',
            'price': 12990000,
            'compare_price': 14990000,
            'brand': 'Vitamix',
            'description': 'Máy xay sinh tố chuyên nghiệp Vitamix E320, 2.2HP',
            'short_description': 'Máy xay Vitamix chuyên nghiệp',
            'stock_quantity': 10,
            'is_featured': False,
        },
        {
            'name': 'Bếp từ đôi Bosch PPI82560MS',
            'slug': 'bep-tu-doi-bosch-ppi82560ms',
            'sku': 'BOSCH-BT-82560',
            'price': 18990000,
            'compare_price': 21990000,
            'brand': 'Bosch',
            'description': 'Bếp từ âm 2 vùng nấu Bosch, công nghệ DirectSelect',
            'short_description': 'Bếp từ Bosch cao cấp',
            'stock_quantity': 8,
            'is_featured': False,
        },
        {
            'name': 'Máy pha cà phê Delonghi Magnifica',
            'slug': 'may-pha-ca-phe-delonghi-magnifica',
            'sku': 'DELONGHI-MAG',
            'price': 15990000,
            'compare_price': 17990000,
            'brand': 'Delonghi',
            'description': 'Máy pha cà phê tự động Delonghi Magnifica, xay và pha tự động',
            'short_description': 'Máy pha cà phê tự động',
            'stock_quantity': 12,
            'is_featured': True,
        },
    ],
    # ============================================
    # 10 SẢN PHẨM MỚI
    # ============================================
    'tablet': [
        {
            'name': 'iPad Pro 12.9 M2 256GB WiFi',
            'slug': 'ipad-pro-12-9-m2-256gb',
            'sku': 'IPAD-PRO-M2-256',
            'price': 28990000,
            'compare_price': 31990000,
            'brand': 'Apple',
            'description': 'iPad Pro 12.9 inch chip M2, màn hình Liquid Retina XDR, hỗ trợ Apple Pencil 2',
            'short_description': 'iPad Pro M2 - Tablet mạnh nhất',
            'stock_quantity': 25,
            'is_featured': True,
        },
        {
            'name': 'Samsung Galaxy Tab S9 Ultra 512GB',
            'slug': 'samsung-galaxy-tab-s9-ultra-512gb',
            'sku': 'SS-TABS9U-512',
            'price': 27990000,
            'compare_price': 29990000,
            'brand': 'Samsung',
            'description': 'Galaxy Tab S9 Ultra màn hình 14.6 inch Dynamic AMOLED 2X, S Pen đi kèm',
            'short_description': 'Galaxy Tab S9 Ultra - Màn hình lớn nhất',
            'stock_quantity': 20,
            'is_featured': True,
        },
    ],
    'phu-kien-dien-thoai': [
        {
            'name': 'AirPods Pro 2 USB-C',
            'slug': 'airpods-pro-2-usb-c',
            'sku': 'AIRPODS-PRO2-C',
            'price': 6290000,
            'compare_price': 6990000,
            'brand': 'Apple',
            'description': 'AirPods Pro 2 cổng USB-C, chống ồn chủ động ANC, Adaptive Audio',
            'short_description': 'AirPods Pro 2 - Tai nghe cao cấp',
            'stock_quantity': 50,
            'is_featured': True,
        },
        {
            'name': 'Samsung Galaxy Watch 6 Classic 47mm',
            'slug': 'samsung-galaxy-watch-6-classic-47mm',
            'sku': 'SS-WATCH6C-47',
            'price': 9990000,
            'compare_price': 10990000,
            'brand': 'Samsung',
            'description': 'Galaxy Watch 6 Classic với vòng bezel xoay, đo huyết áp, ECG',
            'short_description': 'Galaxy Watch 6 Classic - Đồng hồ thông minh',
            'stock_quantity': 35,
            'is_featured': False,
        },
    ],
    'quan-nam': [
        {
            'name': 'Quần Jean Nam Slim Fit Xanh Đậm',
            'slug': 'quan-jean-nam-slim-fit-xanh-dam',
            'sku': 'JEAN-NAM-001',
            'price': 590000,
            'compare_price': 750000,
            'brand': 'Levi\'s',
            'description': 'Quần jean nam form slim fit, chất vải denim co giãn thoải mái',
            'short_description': 'Quần jean Levi\'s slim fit',
            'stock_quantity': 80,
            'is_featured': True,
        },
        {
            'name': 'Quần Kaki Nam Regular Fit Be',
            'slug': 'quan-kaki-nam-regular-fit-be',
            'sku': 'KAKI-NAM-001',
            'price': 450000,
            'compare_price': 550000,
            'brand': 'Dockers',
            'description': 'Quần kaki nam form regular fit, chất liệu cotton pha, phù hợp công sở',
            'short_description': 'Quần kaki Dockers thanh lịch',
            'stock_quantity': 60,
            'is_featured': False,
        },
    ],
    'giay-nam': [
        {
            'name': 'Giày Sneaker Nam Nike Air Max 270',
            'slug': 'giay-sneaker-nam-nike-air-max-270',
            'sku': 'NIKE-AM270-NAM',
            'price': 3290000,
            'compare_price': 3790000,
            'brand': 'Nike',
            'description': 'Giày Nike Air Max 270 đệm khí lớn nhất, êm ái suốt ngày dài',
            'short_description': 'Nike Air Max 270 - Đệm khí tối đa',
            'stock_quantity': 45,
            'is_featured': True,
        },
        {
            'name': 'Giày Tây Nam Da Bò Oxford',
            'slug': 'giay-tay-nam-da-bo-oxford',
            'sku': 'OXFORD-NAM-001',
            'price': 1890000,
            'compare_price': 2290000,
            'brand': 'Pierre Cardin',
            'description': 'Giày tây Oxford da bò thật, đế cao su chống trượt, phù hợp công sở',
            'short_description': 'Giày Oxford da bò cao cấp',
            'stock_quantity': 30,
            'is_featured': False,
        },
    ],
    'giay-nu': [
        {
            'name': 'Giày Cao Gót Nữ Mũi Nhọn 7cm',
            'slug': 'giay-cao-got-nu-mui-nhon-7cm',
            'sku': 'HEEL-NU-001',
            'price': 890000,
            'compare_price': 1090000,
            'brand': 'Juno',
            'description': 'Giày cao gót mũi nhọn 7cm, chất liệu da tổng hợp cao cấp',
            'short_description': 'Giày cao gót thanh lịch',
            'stock_quantity': 55,
            'is_featured': True,
        },
        {
            'name': 'Giày Sneaker Nữ Adidas Ultraboost',
            'slug': 'giay-sneaker-nu-adidas-ultraboost',
            'sku': 'ADIDAS-UB-NU',
            'price': 4290000,
            'compare_price': 4790000,
            'brand': 'Adidas',
            'description': 'Giày Adidas Ultraboost đệm Boost êm ái, phù hợp chạy bộ và đi hàng ngày',
            'short_description': 'Adidas Ultraboost cho nữ',
            'stock_quantity': 40,
            'is_featured': False,
        },
    ],
}


def seed_categories():
    """Tao du lieu mau cho Categories"""
    print("=" * 50)
    print("Seeding Categories...")
    print("=" * 50)

    created_categories = {}

    for cat_data in CATEGORIES:
        # Create parent category
        parent, created = Category.objects.get_or_create(
            slug=cat_data['slug'],
            defaults={
                'name': cat_data['name'],
                'description': cat_data['description'],
                'is_active': True,
                'display_order': CATEGORIES.index(cat_data),
            }
        )
        status = "Created" if created else "Exists"
        print(f"  [{status}] {parent.name}")
        created_categories[cat_data['slug']] = parent

        # Create children
        for i, child_data in enumerate(cat_data.get('children', [])):
            child, created = Category.objects.get_or_create(
                slug=child_data['slug'],
                defaults={
                    'name': child_data['name'],
                    'parent': parent,
                    'is_active': True,
                    'display_order': i,
                }
            )
            status = "Created" if created else "Exists"
            print(f"    [{status}] └── {child.name}")
            created_categories[child_data['slug']] = child

    print(f"\nTotal categories: {len(created_categories)}")
    return created_categories


def seed_products(categories):
    """Tao du lieu mau cho Products"""
    print("\n" + "=" * 50)
    print("Seeding Products...")
    print("=" * 50)

    total_created = 0
    total_exists = 0

    for cat_slug, products in PRODUCTS.items():
        category = categories.get(cat_slug)
        if not category:
            print(f"  [SKIP] Category '{cat_slug}' not found")
            continue

        print(f"\n  Category: {category.name}")

        for product_data in products:
            product, created = Product.objects.get_or_create(
                sku=product_data['sku'],
                defaults={
                    'name': product_data['name'],
                    'slug': product_data['slug'],
                    'price': Decimal(str(product_data['price'])),
                    'compare_price': Decimal(str(product_data['compare_price'])) if product_data.get('compare_price') else None,
                    'brand': product_data['brand'],
                    'description': product_data['description'],
                    'short_description': product_data['short_description'],
                    'stock_quantity': product_data['stock_quantity'],
                    'is_featured': product_data['is_featured'],
                    'category': category,
                    'status': 'active',
                }
            )
            if created:
                total_created += 1
                print(f"    [Created] {product.name}")
            else:
                total_exists += 1
                print(f"    [Exists] {product.name}")

    print(f"\nProducts created: {total_created}")
    print(f"Products existed: {total_exists}")
    print(f"Total products: {total_created + total_exists}")


def run_seed():
    """Chay seeder"""
    print("\n" + "=" * 60)
    print("  PRODUCT SERVICE - DATA SEEDER")
    print("=" * 60)

    # Clear existing data (optional)
    # Product.objects.all().delete()
    # Category.objects.all().delete()

    # Seed data
    categories = seed_categories()
    seed_products(categories)

    print("\n" + "=" * 60)
    print("  SEEDING COMPLETED!")
    print("=" * 60)

    # Statistics
    print(f"\n  Total Categories: {Category.objects.count()}")
    print(f"  Total Products: {Product.objects.count()}")
    print(f"  Featured Products: {Product.objects.filter(is_featured=True).count()}")
    print()


if __name__ == '__main__':
    run_seed()
