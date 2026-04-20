"""
Django Management Command - Seed Data
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
from product_app.models import Category, Product

# Categories data
CATEGORIES = [
    {
        'name': 'Dien thoai & Phu kien',
        'slug': 'dien-thoai-phu-kien',
        'description': 'Dien thoai thong minh, may tinh bang va phu kien',
        'children': [
            {'name': 'Dien thoai Smartphone', 'slug': 'smartphone'},
            {'name': 'May tinh bang', 'slug': 'tablet'},
            {'name': 'Phu kien dien thoai', 'slug': 'phu-kien-dien-thoai'},
        ]
    },
    {
        'name': 'Laptop & May tinh',
        'slug': 'laptop-may-tinh',
        'description': 'Laptop, PC va linh kien may tinh',
        'children': [
            {'name': 'Laptop', 'slug': 'laptop'},
            {'name': 'PC & May tinh de ban', 'slug': 'pc-desktop'},
            {'name': 'Linh kien may tinh', 'slug': 'linh-kien'},
        ]
    },
    {
        'name': 'Thoi trang Nam',
        'slug': 'thoi-trang-nam',
        'description': 'Quan ao, giay dep thoi trang nam',
        'children': [
            {'name': 'Ao nam', 'slug': 'ao-nam'},
            {'name': 'Quan nam', 'slug': 'quan-nam'},
            {'name': 'Giay nam', 'slug': 'giay-nam'},
        ]
    },
    {
        'name': 'Thoi trang Nu',
        'slug': 'thoi-trang-nu',
        'description': 'Quan ao, giay dep thoi trang nu',
        'children': [
            {'name': 'Dam/Vay', 'slug': 'dam-vay'},
            {'name': 'Ao nu', 'slug': 'ao-nu'},
            {'name': 'Giay nu', 'slug': 'giay-nu'},
        ]
    },
    {
        'name': 'Do gia dung',
        'slug': 'do-gia-dung',
        'description': 'Do dung gia dinh, nha bep',
        'children': [
            {'name': 'Do dung nha bep', 'slug': 'do-dung-nha-bep'},
            {'name': 'Do dung phong ngu', 'slug': 'do-dung-phong-ngu'},
            {'name': 'Do dung phong tam', 'slug': 'do-dung-phong-tam'},
        ]
    },
]

# Products data
PRODUCTS = {
    'smartphone': [
        {'name': 'iPhone 15 Pro Max 256GB', 'slug': 'iphone-15-pro-max-256gb', 'sku': 'IP15PM-256', 'price': 34990000, 'compare_price': 36990000, 'brand': 'Apple', 'description': 'iPhone 15 Pro Max voi chip A17 Pro, camera 48MP', 'short_description': 'iPhone 15 Pro Max - Flagship Apple', 'stock_quantity': 50, 'is_featured': True},
        {'name': 'Samsung Galaxy S24 Ultra 512GB', 'slug': 'samsung-galaxy-s24-ultra-512gb', 'sku': 'SS-S24U-512', 'price': 33990000, 'compare_price': 35990000, 'brand': 'Samsung', 'description': 'Samsung Galaxy S24 Ultra voi Galaxy AI, S Pen', 'short_description': 'Galaxy S24 Ultra - AI Phone', 'stock_quantity': 45, 'is_featured': True},
        {'name': 'Xiaomi 14 Ultra 512GB', 'slug': 'xiaomi-14-ultra-512gb', 'sku': 'XM-14U-512', 'price': 23990000, 'compare_price': 25990000, 'brand': 'Xiaomi', 'description': 'Xiaomi 14 Ultra voi camera Leica', 'short_description': 'Xiaomi 14 Ultra - Camera phone', 'stock_quantity': 30, 'is_featured': False},
        {'name': 'OPPO Find X7 Ultra', 'slug': 'oppo-find-x7-ultra', 'sku': 'OPPO-FX7U', 'price': 22990000, 'compare_price': None, 'brand': 'OPPO', 'description': 'OPPO Find X7 Ultra voi camera Hasselblad', 'short_description': 'OPPO Find X7 Ultra', 'stock_quantity': 25, 'is_featured': False},
        {'name': 'Google Pixel 8 Pro 256GB', 'slug': 'google-pixel-8-pro-256gb', 'sku': 'GG-PX8P-256', 'price': 24990000, 'compare_price': 26990000, 'brand': 'Google', 'description': 'Google Pixel 8 Pro voi AI tich hop', 'short_description': 'Pixel 8 Pro - AI Phone', 'stock_quantity': 20, 'is_featured': True},
    ],
    'laptop': [
        {'name': 'MacBook Pro 14 M3 Pro 512GB', 'slug': 'macbook-pro-14-m3-pro-512gb', 'sku': 'MBP14-M3P-512', 'price': 49990000, 'compare_price': 52990000, 'brand': 'Apple', 'description': 'MacBook Pro 14 inch voi chip M3 Pro', 'short_description': 'MacBook Pro M3 Pro', 'stock_quantity': 20, 'is_featured': True},
        {'name': 'Dell XPS 15 9530 Core i7', 'slug': 'dell-xps-15-9530-i7', 'sku': 'DELL-XPS15-I7', 'price': 42990000, 'compare_price': 45990000, 'brand': 'Dell', 'description': 'Dell XPS 15 voi Intel Core i7-13700H', 'short_description': 'Dell XPS 15 cao cap', 'stock_quantity': 15, 'is_featured': True},
        {'name': 'ASUS ROG Strix G16 RTX 4070', 'slug': 'asus-rog-strix-g16-rtx4070', 'sku': 'ASUS-ROG-G16', 'price': 38990000, 'compare_price': 41990000, 'brand': 'ASUS', 'description': 'ASUS ROG Strix G16 voi RTX 4070', 'short_description': 'ROG Strix G16 Gaming', 'stock_quantity': 25, 'is_featured': False},
        {'name': 'Lenovo ThinkPad X1 Carbon Gen 11', 'slug': 'lenovo-thinkpad-x1-carbon-gen11', 'sku': 'LEN-X1C-G11', 'price': 35990000, 'compare_price': None, 'brand': 'Lenovo', 'description': 'ThinkPad X1 Carbon voi Core i7 vPro', 'short_description': 'ThinkPad X1 Carbon', 'stock_quantity': 18, 'is_featured': False},
        {'name': 'HP Spectre x360 14 OLED', 'slug': 'hp-spectre-x360-14-oled', 'sku': 'HP-SPX360-14', 'price': 32990000, 'compare_price': 34990000, 'brand': 'HP', 'description': 'HP Spectre x360 14 man hinh OLED', 'short_description': 'Spectre x360 2-in-1', 'stock_quantity': 12, 'is_featured': True},
    ],
    'ao-nam': [
        {'name': 'Ao Polo Nam Cotton Premium', 'slug': 'ao-polo-nam-cotton-premium', 'sku': 'POLO-NAM-001', 'price': 450000, 'compare_price': 550000, 'brand': 'Local Brand', 'description': 'Ao polo nam chat lieu cotton cao cap', 'short_description': 'Ao polo cotton cao cap', 'stock_quantity': 100, 'is_featured': True},
        {'name': 'Ao So Mi Nam Slim Fit Trang', 'slug': 'ao-so-mi-nam-slim-fit-trang', 'sku': 'SOMI-NAM-001', 'price': 380000, 'compare_price': 450000, 'brand': 'Viet Tien', 'description': 'Ao so mi nam form slim fit', 'short_description': 'Ao so mi trang slim fit', 'stock_quantity': 80, 'is_featured': False},
        {'name': 'Ao Thun Nam Basic Den', 'slug': 'ao-thun-nam-basic-den', 'sku': 'THUN-NAM-001', 'price': 199000, 'compare_price': 250000, 'brand': 'Coolmate', 'description': 'Ao thun basic nam mau den', 'short_description': 'Ao thun basic den', 'stock_quantity': 200, 'is_featured': False},
        {'name': 'Ao Khoac Bomber Nam', 'slug': 'ao-khoac-bomber-nam', 'sku': 'BOMBER-NAM-001', 'price': 650000, 'compare_price': 800000, 'brand': 'MLB', 'description': 'Ao khoac bomber nam streetwear', 'short_description': 'Bomber jacket', 'stock_quantity': 50, 'is_featured': True},
        {'name': 'Ao Hoodie Nam Oversize', 'slug': 'ao-hoodie-nam-oversize', 'sku': 'HOODIE-NAM-001', 'price': 520000, 'compare_price': 620000, 'brand': 'Uniqlo', 'description': 'Ao hoodie nam form oversize', 'short_description': 'Hoodie oversize', 'stock_quantity': 75, 'is_featured': False},
    ],
    'dam-vay': [
        {'name': 'Dam Maxi Hoa Nhi Vintage', 'slug': 'dam-maxi-hoa-nhi-vintage', 'sku': 'DAM-MAXI-001', 'price': 550000, 'compare_price': 700000, 'brand': 'Zara', 'description': 'Dam maxi hoa tiet hoa nhi vintage', 'short_description': 'Dam maxi hoa vintage', 'stock_quantity': 60, 'is_featured': True},
        {'name': 'Vay Cong So A-line Thanh Lich', 'slug': 'vay-cong-so-a-line', 'sku': 'VAY-CS-001', 'price': 480000, 'compare_price': 580000, 'brand': 'IVY Moda', 'description': 'Vay cong so form A-line', 'short_description': 'Vay cong so thanh lich', 'stock_quantity': 45, 'is_featured': False},
        {'name': 'Dam Body Om Sat Quyen Ru', 'slug': 'dam-body-om-sat-quyen-ru', 'sku': 'DAM-BODY-001', 'price': 420000, 'compare_price': 520000, 'brand': 'Mango', 'description': 'Dam body om sat ton dang', 'short_description': 'Dam body quyen ru', 'stock_quantity': 35, 'is_featured': True},
        {'name': 'Vay Midi Xep Ly Han Quoc', 'slug': 'vay-midi-xep-ly-han-quoc', 'sku': 'VAY-MIDI-001', 'price': 390000, 'compare_price': 490000, 'brand': 'Stylenanda', 'description': 'Vay midi xep ly phong cach Han Quoc', 'short_description': 'Vay midi Han Quoc', 'stock_quantity': 55, 'is_featured': False},
        {'name': 'Dam So Mi Caro Basic', 'slug': 'dam-so-mi-caro-basic', 'sku': 'DAM-SOMI-001', 'price': 350000, 'compare_price': None, 'brand': 'H&M', 'description': 'Dam so mi hoa tiet caro casual', 'short_description': 'Dam so mi caro', 'stock_quantity': 70, 'is_featured': False},
    ],
    'do-dung-nha-bep': [
        {'name': 'Noi chien khong dau Philips 6.2L', 'slug': 'noi-chien-khong-dau-philips-6l', 'sku': 'PHILIPS-AF-6L', 'price': 3990000, 'compare_price': 4500000, 'brand': 'Philips', 'description': 'Noi chien khong dau Philips 6.2L RapidAir', 'short_description': 'Air Fryer Philips 6.2L', 'stock_quantity': 30, 'is_featured': True},
        {'name': 'Bo noi inox 5 chiec Fissler', 'slug': 'bo-noi-inox-5-chiec-fissler', 'sku': 'FISSLER-SET5', 'price': 8990000, 'compare_price': 10990000, 'brand': 'Fissler', 'description': 'Bo noi inox cao cap Fissler Germany', 'short_description': 'Bo noi inox Duc', 'stock_quantity': 15, 'is_featured': True},
        {'name': 'May xay sinh to Vitamix E320', 'slug': 'may-xay-sinh-to-vitamix-e320', 'sku': 'VITAMIX-E320', 'price': 12990000, 'compare_price': 14990000, 'brand': 'Vitamix', 'description': 'May xay sinh to chuyen nghiep 2.2HP', 'short_description': 'May xay Vitamix', 'stock_quantity': 10, 'is_featured': False},
        {'name': 'Bep tu doi Bosch PPI82560MS', 'slug': 'bep-tu-doi-bosch-ppi82560ms', 'sku': 'BOSCH-BT-82560', 'price': 18990000, 'compare_price': 21990000, 'brand': 'Bosch', 'description': 'Bep tu am 2 vung nau Bosch', 'short_description': 'Bep tu Bosch', 'stock_quantity': 8, 'is_featured': False},
        {'name': 'May pha ca phe Delonghi Magnifica', 'slug': 'may-pha-ca-phe-delonghi-magnifica', 'sku': 'DELONGHI-MAG', 'price': 15990000, 'compare_price': 17990000, 'brand': 'Delonghi', 'description': 'May pha ca phe tu dong Delonghi', 'short_description': 'May pha cafe tu dong', 'stock_quantity': 12, 'is_featured': True},
    ],
}


class Command(BaseCommand):
    help = 'Seed database with sample data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('  PRODUCT SERVICE - DATA SEEDER'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        categories = self.seed_categories()
        self.seed_products(categories)

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('  SEEDING COMPLETED!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f"\n  Total Categories: {Category.objects.count()}")
        self.stdout.write(f"  Total Products: {Product.objects.count()}")
        self.stdout.write(f"  Featured Products: {Product.objects.filter(is_featured=True).count()}\n")

    def seed_categories(self):
        self.stdout.write(self.style.SUCCESS('\nSeeding Categories...'))
        created_categories = {}

        for i, cat_data in enumerate(CATEGORIES):
            parent, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description'],
                    'is_active': True,
                    'display_order': i,
                }
            )
            status = 'Created' if created else 'Exists'
            self.stdout.write(f"  [{status}] {parent.name}")
            created_categories[cat_data['slug']] = parent

            for j, child_data in enumerate(cat_data.get('children', [])):
                child, created = Category.objects.get_or_create(
                    slug=child_data['slug'],
                    defaults={
                        'name': child_data['name'],
                        'parent': parent,
                        'is_active': True,
                        'display_order': j,
                    }
                )
                status = 'Created' if created else 'Exists'
                self.stdout.write(f"    [{status}] -- {child.name}")
                created_categories[child_data['slug']] = child

        return created_categories

    def seed_products(self, categories):
        self.stdout.write(self.style.SUCCESS('\nSeeding Products...'))
        total_created = 0

        for cat_slug, products in PRODUCTS.items():
            category = categories.get(cat_slug)
            if not category:
                continue

            self.stdout.write(f"\n  Category: {category.name}")

            for p in products:
                product, created = Product.objects.get_or_create(
                    sku=p['sku'],
                    defaults={
                        'name': p['name'],
                        'slug': p['slug'],
                        'price': Decimal(str(p['price'])),
                        'compare_price': Decimal(str(p['compare_price'])) if p.get('compare_price') else None,
                        'brand': p['brand'],
                        'description': p['description'],
                        'short_description': p['short_description'],
                        'stock_quantity': p['stock_quantity'],
                        'is_featured': p['is_featured'],
                        'category': category,
                        'status': 'active',
                    }
                )
                if created:
                    total_created += 1
                    self.stdout.write(f"    [+] {p['name']}")
                else:
                    self.stdout.write(f"    [=] {p['name']}")

        self.stdout.write(f"\n  Products created: {total_created}")
