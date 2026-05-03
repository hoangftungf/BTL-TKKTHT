"""
Management command to generate sample products for all categories
"""

import uuid
import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from product_app.models import Category, Product


# Product templates for each category
PRODUCT_TEMPLATES = {
    'tv': [
        {'name': 'Samsung QLED 4K 55 inch QA55Q60B', 'price': 15990000, 'brand': 'Samsung', 'desc': 'Smart TV QLED 4K, Quantum HDR, Gaming Hub'},
        {'name': 'LG OLED 65 inch OLED65C3PSA', 'price': 42990000, 'brand': 'LG', 'desc': 'OLED evo, Dolby Vision IQ, webOS 23'},
        {'name': 'Sony Bravia XR 55 inch XR-55X90L', 'price': 25990000, 'brand': 'Sony', 'desc': 'Full Array LED, Cognitive Processor XR'},
        {'name': 'TCL QLED 4K 65 inch 65C735', 'price': 16990000, 'brand': 'TCL', 'desc': 'QLED, Google TV, Game Master Pro'},
    ],
    'refrigerator': [
        {'name': 'Samsung Inverter 380L RT38K5982DX', 'price': 12990000, 'brand': 'Samsung', 'desc': 'Twin Cooling Plus, Digital Inverter'},
        {'name': 'LG Inverter 635L GR-D257JS', 'price': 28990000, 'brand': 'LG', 'desc': 'Side by Side, Door-in-Door, Linear Cooling'},
        {'name': 'Panasonic Inverter 322L NR-BV360GKVN', 'price': 11490000, 'brand': 'Panasonic', 'desc': 'Econavi, Ag Clean'},
        {'name': 'Hitachi Inverter 540L R-FW690PGV7X', 'price': 32990000, 'brand': 'Hitachi', 'desc': 'French Door, Vacuum Compartment'},
    ],
    'washing-machine': [
        {'name': 'Samsung Inverter 10kg WW10TP44DSH', 'price': 11990000, 'brand': 'Samsung', 'desc': 'AI Wash, EcoBubble, Steam Wash'},
        {'name': 'LG Inverter 9kg FV1409S4W', 'price': 9990000, 'brand': 'LG', 'desc': 'AI DD, Steam+, TurboWash 360'},
        {'name': 'Electrolux Inverter 11kg EWF1141SESA', 'price': 14990000, 'brand': 'Electrolux', 'desc': 'UltraMix, Vapour Care, SensorWash'},
        {'name': 'Panasonic Inverter 10kg NA-V10FX2LVT', 'price': 12490000, 'brand': 'Panasonic', 'desc': 'StainMaster+, Blue Ag+'},
    ],
    'air-conditioner': [
        {'name': 'Daikin Inverter 1.5HP FTKZ35VVMV', 'price': 18990000, 'brand': 'Daikin', 'desc': 'Inverter, Streamer, Coanda'},
        {'name': 'Panasonic Inverter 2HP CU/CS-XU18ZKH-8', 'price': 22990000, 'brand': 'Panasonic', 'desc': 'nanoe X, Inverter, Sky Series'},
        {'name': 'LG Inverter 1HP V10WIN1', 'price': 8990000, 'brand': 'LG', 'desc': 'Dual Inverter, UVnano, ThinQ'},
        {'name': 'Samsung Inverter 1.5HP AR13CYHAAWKNSV', 'price': 11990000, 'brand': 'Samsung', 'desc': 'WindFree, Digital Inverter Boost'},
    ],
    'laptop': [
        {'name': 'ASUS ZenBook 14 OLED UX3402VA', 'price': 27990000, 'brand': 'ASUS', 'desc': 'Core i5-1340P, 16GB RAM, 512GB SSD, OLED 2.8K'},
        {'name': 'HP Envy x360 15-fe0056TU', 'price': 24990000, 'brand': 'HP', 'desc': 'Core i7-1355U, 16GB RAM, 512GB SSD, Touch'},
        {'name': 'Acer Swift Go 14 SFG14-71-51BD', 'price': 19990000, 'brand': 'Acer', 'desc': 'Core i5-1335U, 16GB RAM, 512GB SSD, 2.8K OLED'},
        {'name': 'MSI Prestige 14 Evo A13M-212VN', 'price': 26990000, 'brand': 'MSI', 'desc': 'Core i7-1360P, 16GB RAM, 512GB SSD'},
    ],
    'desktop-pc': [
        {'name': 'Dell OptiPlex 7010 Tower', 'price': 18990000, 'brand': 'Dell', 'desc': 'Core i5-13500, 8GB RAM, 256GB SSD'},
        {'name': 'HP ProDesk 400 G9 SFF', 'price': 15990000, 'brand': 'HP', 'desc': 'Core i5-12500, 8GB RAM, 256GB SSD'},
        {'name': 'Lenovo ThinkCentre M70q Gen 3', 'price': 14990000, 'brand': 'Lenovo', 'desc': 'Core i5-12400T, 8GB RAM, 256GB SSD, Tiny'},
        {'name': 'Apple Mac Mini M2 256GB', 'price': 14990000, 'brand': 'Apple', 'desc': 'Chip M2, 8GB RAM, 256GB SSD'},
    ],
    'components': [
        {'name': 'Intel Core i7-14700K', 'price': 11990000, 'brand': 'Intel', 'desc': 'LGA 1700, 20 cores, 5.6GHz Turbo'},
        {'name': 'AMD Ryzen 7 7800X3D', 'price': 12490000, 'brand': 'AMD', 'desc': 'AM5, 8 cores, 3D V-Cache'},
        {'name': 'NVIDIA GeForce RTX 4070 Super', 'price': 16990000, 'brand': 'NVIDIA', 'desc': '12GB GDDR6X, DLSS 3'},
        {'name': 'Samsung 990 Pro 2TB NVMe', 'price': 5990000, 'brand': 'Samsung', 'desc': 'PCIe 4.0, 7450MB/s Read'},
    ],
    'smartphone': [
        {'name': 'Samsung Galaxy S24 Ultra 256GB', 'price': 33990000, 'brand': 'Samsung', 'desc': 'Snapdragon 8 Gen 3, 200MP Camera, S Pen'},
        {'name': 'iPhone 15 Pro 256GB', 'price': 30990000, 'brand': 'Apple', 'desc': 'A17 Pro, Titanium Design, Action Button'},
        {'name': 'Xiaomi 14 Pro 512GB', 'price': 24990000, 'brand': 'Xiaomi', 'desc': 'Snapdragon 8 Gen 3, Leica Camera'},
        {'name': 'OPPO Find X7 Ultra 256GB', 'price': 27990000, 'brand': 'OPPO', 'desc': 'Dual Periscope, Hasselblad'},
    ],
    'tablet': [
        {'name': 'iPad Air M2 11 inch 128GB', 'price': 16990000, 'brand': 'Apple', 'desc': 'Chip M2, Liquid Retina, USB-C'},
        {'name': 'Samsung Galaxy Tab S9+ 256GB', 'price': 24990000, 'brand': 'Samsung', 'desc': 'Snapdragon 8 Gen 2, 12.4 inch AMOLED'},
        {'name': 'Xiaomi Pad 6 Pro 256GB', 'price': 11990000, 'brand': 'Xiaomi', 'desc': 'Snapdragon 8+ Gen 1, 144Hz'},
        {'name': 'Lenovo Tab P12 Pro 256GB', 'price': 18990000, 'brand': 'Lenovo', 'desc': 'Snapdragon 870, OLED 12.6 inch'},
    ],
    'phone-accessories': [
        {'name': 'Apple AirPods Pro 2 USB-C', 'price': 6290000, 'brand': 'Apple', 'desc': 'Active Noise Cancellation, H2 Chip'},
        {'name': 'Samsung Galaxy Buds3 Pro', 'price': 5490000, 'brand': 'Samsung', 'desc': 'ANC, 360 Audio, IP57'},
        {'name': 'Anker 737 Power Bank 24000mAh', 'price': 2990000, 'brand': 'Anker', 'desc': '140W Output, PD 3.1'},
        {'name': 'Spigen Ultra Hybrid iPhone 15 Pro', 'price': 590000, 'brand': 'Spigen', 'desc': 'Military Grade Protection, Clear'},
    ],
    'shirt-men': [
        {'name': 'Áo Sơ Mi Nam Dài Tay Oxford Trắng', 'price': 450000, 'brand': 'Aristino', 'desc': 'Cotton Oxford, Regular Fit'},
        {'name': 'Áo Polo Nam Cotton Pique Xanh Navy', 'price': 380000, 'brand': 'Routine', 'desc': '100% Cotton, Cổ bẻ'},
        {'name': 'Áo Thun Nam Basic Đen', 'price': 250000, 'brand': 'Coolmate', 'desc': 'Cotton Compact, Regular Fit'},
        {'name': 'Áo Hoodie Nam Oversize Xám', 'price': 520000, 'brand': 'Uniqlo', 'desc': 'French Terry, Relaxed Fit'},
    ],
    'pants-men': [
        {'name': 'Quần Jean Nam Slim Fit Xanh Đậm', 'price': 590000, 'brand': "Levi's", 'desc': '511 Slim, Stretch Denim'},
        {'name': 'Quần Kaki Nam Regular Fit Be', 'price': 450000, 'brand': 'Dockers', 'desc': 'Smart 360 Flex, Easy Care'},
        {'name': 'Quần Jogger Nam Thể Thao Đen', 'price': 380000, 'brand': 'Adidas', 'desc': 'Essentials Fleece, Tapered'},
        {'name': 'Quần Short Nam Kaki Xanh Rêu', 'price': 350000, 'brand': 'GAP', 'desc': 'Vintage Wash, 10 inch inseam'},
    ],
    'shoes-men': [
        {'name': 'Giày Sneaker Nam Nike Air Max 90', 'price': 3590000, 'brand': 'Nike', 'desc': 'Air Max, Leather Upper'},
        {'name': 'Giày Chạy Bộ Nam Adidas Ultraboost', 'price': 4290000, 'brand': 'Adidas', 'desc': 'Boost Midsole, Primeknit'},
        {'name': 'Giày Tây Nam Oxford Da Bò Đen', 'price': 1890000, 'brand': 'Pierre Cardin', 'desc': 'Full Grain Leather, Goodyear Welt'},
        {'name': 'Giày Loafer Nam Da Nâu', 'price': 1590000, 'brand': 'Bata', 'desc': 'Genuine Leather, Cushioned Insole'},
    ],
    'dress': [
        {'name': 'Đầm Maxi Hoa Nhí Vintage', 'price': 550000, 'brand': 'Zara', 'desc': 'Voan Hoa, Tay Phồng'},
        {'name': 'Váy Midi Xếp Ly Hàn Quốc', 'price': 420000, 'brand': 'Stylenanda', 'desc': 'Chiffon, Lưng Cao'},
        {'name': 'Đầm Body Ôm Sát Quyến Rũ', 'price': 480000, 'brand': 'Mango', 'desc': 'Ribbed Knit, Midi Length'},
        {'name': 'Váy Công Sở A-line Thanh Lịch', 'price': 390000, 'brand': 'IVY Moda', 'desc': 'Polyester Blend, Knee Length'},
    ],
    'tops-women': [
        {'name': 'Áo Blouse Nữ Cổ V Trắng', 'price': 350000, 'brand': 'H&M', 'desc': 'Voan Mỏng, Tay Dài'},
        {'name': 'Áo Croptop Nữ Thể Thao Đen', 'price': 280000, 'brand': 'Nike', 'desc': 'Dri-FIT, High Support'},
        {'name': 'Áo Sơ Mi Nữ Oversize Kẻ Sọc', 'price': 420000, 'brand': 'Zara', 'desc': 'Cotton Blend, Relaxed Fit'},
        {'name': 'Áo Len Nữ Cổ Tròn Hồng Pastel', 'price': 480000, 'brand': 'Uniqlo', 'desc': '100% Cashmere, Lightweight'},
    ],
    'heels': [
        {'name': 'Giày Cao Gót Nữ Mũi Nhọn 9cm', 'price': 890000, 'brand': 'Juno', 'desc': 'Da Tổng Hợp, Gót Vuông'},
        {'name': 'Sandal Cao Gót Nữ Quai Mảnh 7cm', 'price': 750000, 'brand': 'Vascara', 'desc': 'PU Cao Cấp, Đế Đúc'},
        {'name': 'Giày Pump Nữ Da Bò Đen 5cm', 'price': 1290000, 'brand': 'Charles & Keith', 'desc': 'Genuine Leather, Block Heel'},
        {'name': 'Giày Slingback Nữ Mũi Vuông 6cm', 'price': 680000, 'brand': 'Zara', 'desc': 'Faux Leather, Kitten Heel'},
    ],
    'lipstick': [
        {'name': 'Son Thỏi MAC Matte Lipstick Ruby Woo', 'price': 650000, 'brand': 'MAC', 'desc': 'Retro Matte, Vivid Red'},
        {'name': 'Son Kem Lì 3CE Velvet Lip Tint', 'price': 380000, 'brand': '3CE', 'desc': 'Soft Matte, Long Lasting'},
        {'name': 'Son Dưỡng Dior Lip Glow', 'price': 990000, 'brand': 'Dior', 'desc': 'Color Reviver, Natural Glow'},
        {'name': 'Son Thỏi YSL Rouge Pur Couture', 'price': 1050000, 'brand': 'YSL', 'desc': 'Satin Finish, Hydrating'},
    ],
    'foundation': [
        {'name': 'Kem Nền Estee Lauder Double Wear', 'price': 1350000, 'brand': 'Estee Lauder', 'desc': '24H Stay-in-Place, Full Coverage'},
        {'name': 'Cushion Laneige Neo Cushion Matte', 'price': 890000, 'brand': 'Laneige', 'desc': 'SPF42, Matte Finish'},
        {'name': 'BB Cream Missha M Perfect Cover', 'price': 380000, 'brand': 'Missha', 'desc': 'SPF42, Natural Coverage'},
        {'name': 'Kem Nền MAC Studio Fix Fluid', 'price': 950000, 'brand': 'MAC', 'desc': 'SPF15, Buildable Coverage'},
    ],
    'skincare': [
        {'name': 'Serum Vitamin C SkinCeuticals CE Ferulic', 'price': 3990000, 'brand': 'SkinCeuticals', 'desc': '15% Vitamin C, Antioxidant'},
        {'name': 'Kem Dưỡng Ẩm La Roche-Posay Cicaplast', 'price': 450000, 'brand': 'La Roche-Posay', 'desc': 'B5 Baume, Soothing'},
        {'name': 'Toner Klairs Supple Preparation', 'price': 480000, 'brand': 'Klairs', 'desc': 'Hydrating, pH Balanced'},
        {'name': 'Sữa Rửa Mặt CeraVe Foaming Cleanser', 'price': 350000, 'brand': 'CeraVe', 'desc': 'Ceramides, Non-Comedogenic'},
    ],
    'cookware': [
        {'name': 'Bộ Nồi Inox 5 Chiếc Fissler', 'price': 8990000, 'brand': 'Fissler', 'desc': 'Inox 18/10, Made in Germany'},
        {'name': 'Chảo Chống Dính Tefal Unlimited 28cm', 'price': 1290000, 'brand': 'Tefal', 'desc': 'Titanium Excellence, Thermo-Spot'},
        {'name': 'Nồi Áp Suất Điện Instant Pot Duo 6L', 'price': 2990000, 'brand': 'Instant Pot', 'desc': '7-in-1, Programmable'},
        {'name': 'Bộ Dao Zwilling Pro 7 Món', 'price': 6990000, 'brand': 'Zwilling', 'desc': 'Forged Steel, Ice-Hardened'},
    ],
    'kitchen-appliances': [
        {'name': 'Máy Pha Cà Phê DeLonghi Magnifica S', 'price': 15990000, 'brand': 'DeLonghi', 'desc': 'Tự Động, Xay Hạt'},
        {'name': 'Nồi Chiên Không Dầu Philips XXL 7.3L', 'price': 5990000, 'brand': 'Philips', 'desc': 'Rapid Air, Digital'},
        {'name': 'Máy Xay Sinh Tố Vitamix E310', 'price': 12990000, 'brand': 'Vitamix', 'desc': '10 Speed, 1.4L'},
        {'name': 'Lò Vi Sóng Panasonic NN-ST65JWYPQ', 'price': 3290000, 'brand': 'Panasonic', 'desc': 'Inverter, 32L'},
    ],
    'furniture': [
        {'name': 'Ghế Công Thái Học Ergohuman Elite', 'price': 15990000, 'brand': 'Ergohuman', 'desc': 'Mesh, Adjustable Lumbar'},
        {'name': 'Bàn Làm Việc Nâng Hạ Điện FlexiSpot', 'price': 8990000, 'brand': 'FlexiSpot', 'desc': 'Electric Standing Desk, 120x60cm'},
        {'name': 'Kệ Sách Gỗ 5 Tầng IKEA Billy', 'price': 2990000, 'brand': 'IKEA', 'desc': 'Particleboard, 80x28x202cm'},
        {'name': 'Sofa Góc L Vải Bố Xám', 'price': 12990000, 'brand': 'Nội Thất Hòa Phát', 'desc': 'Vải Bố Cao Cấp, 2.8m'},
    ],
    'gym-equipment': [
        {'name': 'Máy Chạy Bộ Điện Elipsport Premium', 'price': 18990000, 'brand': 'Elipsport', 'desc': '3.0HP, Màn Hình LCD'},
        {'name': 'Bộ Tạ Tay Cao Su 20kg Adidas', 'price': 1990000, 'brand': 'Adidas', 'desc': 'Rubber Coated, 2.5-10kg'},
        {'name': 'Xe Đạp Tập Thể Dục Spinning Kingsport', 'price': 5990000, 'brand': 'Kingsport', 'desc': 'Flywheel 15kg, LCD'},
        {'name': 'Thảm Tập Yoga TPE 2 Lớp 6mm', 'price': 390000, 'brand': 'Reebok', 'desc': 'Eco-Friendly, Non-Slip'},
    ],
    'outdoor-gear': [
        {'name': 'Lều Cắm Trại 4 Người Naturehike', 'price': 2990000, 'brand': 'Naturehike', 'desc': 'Ultralight, Waterproof 3000mm'},
        {'name': 'Balo Leo Núi Osprey Atmos AG 65L', 'price': 6990000, 'brand': 'Osprey', 'desc': 'Anti-Gravity Suspension'},
        {'name': 'Túi Ngủ Lông Vũ The North Face -10°C', 'price': 4990000, 'brand': 'The North Face', 'desc': '800 Fill Power Down'},
        {'name': 'Đèn Pin Siêu Sáng Fenix PD36R', 'price': 2290000, 'brand': 'Fenix', 'desc': '1600 Lumens, USB-C'},
    ],
    'watches': [
        {'name': 'Đồng Hồ Nam Citizen Eco-Drive', 'price': 5990000, 'brand': 'Citizen', 'desc': 'Solar Powered, Sapphire Crystal'},
        {'name': 'Đồng Hồ Nữ Daniel Wellington Petite', 'price': 3990000, 'brand': 'Daniel Wellington', 'desc': 'Minimalist, Japanese Quartz'},
        {'name': 'Smartwatch Garmin Venu 3', 'price': 12990000, 'brand': 'Garmin', 'desc': 'AMOLED, Health Monitoring'},
        {'name': 'Đồng Hồ Nam Seiko Presage SRPB41J1', 'price': 8990000, 'brand': 'Seiko', 'desc': 'Automatic, Cocktail Time'},
    ],
    'bags': [
        {'name': 'Balo Laptop Samsonite Red 15.6 inch', 'price': 2990000, 'brand': 'Samsonite', 'desc': 'Water Resistant, TSA Lock'},
        {'name': 'Túi Xách Nữ Coach Willow Tote', 'price': 8990000, 'brand': 'Coach', 'desc': 'Polished Pebble Leather'},
        {'name': 'Túi Đeo Chéo Nam Pedro Saffiano', 'price': 1590000, 'brand': 'Pedro', 'desc': 'Saffiano Leather, Compact'},
        {'name': 'Vali Kéo American Tourister 24 inch', 'price': 2490000, 'brand': 'American Tourister', 'desc': 'PC, TSA Lock, Spinner'},
    ],
    'books': [
        {'name': 'Đắc Nhân Tâm - Dale Carnegie', 'price': 108000, 'brand': 'NXB Tổng Hợp', 'desc': 'Bản Dịch Mới, Bìa Cứng'},
        {'name': 'Nhà Giả Kim - Paulo Coelho', 'price': 79000, 'brand': 'NXB Hội Nhà Văn', 'desc': 'Tiểu Thuyết, Bìa Mềm'},
        {'name': 'Sapiens: Lược Sử Loài Người', 'price': 209000, 'brand': 'NXB Tri Thức', 'desc': 'Yuval Noah Harari, Bìa Cứng'},
        {'name': 'Atomic Habits - James Clear', 'price': 168000, 'brand': 'NXB Thế Giới', 'desc': 'Thói Quen Nguyên Tử, Bìa Mềm'},
    ],
    'stationery': [
        {'name': 'Bút Bi Cao Cấp Parker Jotter', 'price': 490000, 'brand': 'Parker', 'desc': 'Stainless Steel, Blue Ink'},
        {'name': 'Sổ Tay Moleskine Classic Large', 'price': 590000, 'brand': 'Moleskine', 'desc': 'Ruled, Hard Cover, 240 Pages'},
        {'name': 'Bộ Bút Lông Màu Faber-Castell 48 Cây', 'price': 350000, 'brand': 'Faber-Castell', 'desc': 'Connector Pens, Washable'},
        {'name': 'Máy Tính Casio FX-580VN X', 'price': 650000, 'brand': 'Casio', 'desc': '521 Functions, Scientific'},
    ],
}


class Command(BaseCommand):
    help = 'Generate sample products for all categories'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Total number of products to generate (default: 100)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes',
        )

    def handle(self, *args, **options):
        total_count = options['count']
        dry_run = options['dry_run']

        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write(self.style.NOTICE(f'Generate {total_count} Sample Products'))
        self.stdout.write(self.style.NOTICE('=' * 60))

        # Get all subcategories (level 1)
        subcategories = Category.objects.filter(level=1).order_by('parent__display_order', 'display_order')
        subcat_count = subcategories.count()

        if subcat_count == 0:
            self.stdout.write(self.style.ERROR('No subcategories found! Run rebuild_categories first.'))
            return

        # Calculate products per category
        products_per_cat = total_count // subcat_count
        extra = total_count % subcat_count

        self.stdout.write(f'\nFound {subcat_count} subcategories')
        self.stdout.write(f'Products per category: {products_per_cat} (+ {extra} extra distributed)')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] No changes will be made\n'))
            for cat in subcategories:
                templates = PRODUCT_TEMPLATES.get(cat.slug, [])
                self.stdout.write(f'  {cat.parent.name} > {cat.name}: {len(templates)} templates')
            return

        # Generate products
        created_count = 0
        extra_distributed = 0

        with transaction.atomic():
            for cat in subcategories:
                templates = PRODUCT_TEMPLATES.get(cat.slug, [])

                if not templates:
                    self.stdout.write(self.style.WARNING(f'  No templates for {cat.slug}, skipping'))
                    continue

                # Determine how many to create for this category
                count_for_cat = products_per_cat
                if extra_distributed < extra:
                    count_for_cat += 1
                    extra_distributed += 1

                self.stdout.write(f'\n{cat.parent.name} > {cat.name}:')

                for i in range(count_for_cat):
                    template = templates[i % len(templates)]

                    # Add variation to name if reusing template
                    name = template['name']
                    if i >= len(templates):
                        variations = ['Pro', 'Plus', 'Max', 'Ultra', 'Lite', 'Mini', 'SE', 'New']
                        name = f"{template['name']} {random.choice(variations)}"

                    # Vary price slightly
                    base_price = template['price']
                    price_variation = random.uniform(0.9, 1.1)
                    price = Decimal(str(int(base_price * price_variation)))

                    # Create unique SKU
                    sku = f"{cat.slug.upper()[:3]}-{uuid.uuid4().hex[:8].upper()}"

                    # Create unique slug
                    base_slug = slugify(name)
                    slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"

                    # Create product
                    product = Product.objects.create(
                        name=name,
                        slug=slug,
                        description=template['desc'],
                        short_description=template['desc'][:100],
                        sku=sku,
                        price=price,
                        compare_price=price * Decimal('1.15') if random.random() > 0.5 else None,
                        category=cat,
                        brand=template['brand'],
                        status='active',
                        stock_quantity=random.randint(10, 200),
                        is_featured=random.random() > 0.8,
                    )
                    created_count += 1
                    self.stdout.write(f'  + {product.name}')

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} products'))
        self.stdout.write('=' * 60)

        # Print distribution
        self.stdout.write('\nProducts per category:')
        for cat in Category.objects.filter(level=0).order_by('display_order'):
            cat_total = Product.objects.filter(category__parent=cat).count()
            self.stdout.write(f'\n  {cat.name}: {cat_total} products')
            for child in cat.children.order_by('display_order'):
                child_count = Product.objects.filter(category=child).count()
                self.stdout.write(f'    - {child.name}: {child_count}')

        total = Product.objects.count()
        self.stdout.write(f'\n\nTotal products in database: {total}')
