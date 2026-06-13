import os
import sys
import django
from pathlib import Path
from decimal import Decimal

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'product_project.settings')
django.setup()

from product_app.models import Product, ProductVariant

def run():
    print("=" * 60)
    print("  SEEDING DETAILED SPECIFICATIONS AND VARIANTS")
    print("=" * 60)

    # 1. Xiaomi 14 Ultra 512GB
    try:
        p_xiaomi = Product.objects.get(sku='XM-14U-512')
        p_xiaomi.specifications = {
            "Màn hình": "6.73 inch LTPO AMOLED, 120Hz, Dolby Vision, HDR10+",
            "Hệ điều hành": "Android 14, HyperOS",
            "Chipset": "Qualcomm Snapdragon 8 Gen 3 (4 nm)",
            "CPU": "Octa-core",
            "GPU": "Adreno 750",
            "Bộ nhớ trong": "512GB UFS 4.0",
            "RAM": "16GB LPDDR5X",
            "Camera sau": "Bộ 4 camera Leica 50MP, zoom quang 5x, quay video 8K",
            "Camera trước": "32 MP, f/2.0, quay video 4K",
            "Pin": "5000 mAh",
            "Sạc nhanh": "Sạc nhanh 90W có dây, sạc nhanh không dây 80W"
        }
        p_xiaomi.save()
        print(f"[Updated specifications] {p_xiaomi.name}")

        # Delete existing variants if any
        ProductVariant.objects.filter(product=p_xiaomi).delete()

        # Create Variants
        v1 = ProductVariant.objects.create(
            product=p_xiaomi,
            name="Xiaomi 14 Ultra 512GB - Màu Đen",
            sku="XM-14U-512-BLACK",
            price=Decimal("23990000"),
            stock_quantity=15,
            attributes={"color": "Đen", "storage": "512GB", "ram": "16GB"},
            is_active=True
        )
        v2 = ProductVariant.objects.create(
            product=p_xiaomi,
            name="Xiaomi 14 Ultra 512GB - Màu Trắng",
            sku="XM-14U-512-WHITE",
            price=Decimal("23990000"),
            stock_quantity=15,
            attributes={"color": "Trắng", "storage": "512GB", "ram": "16GB"},
            is_active=True
        )
        print(f"  Created variants: {v1.sku}, {v2.sku}")
    except Product.DoesNotExist:
        print("  [ERROR] Xiaomi 14 Ultra not found in DB")

    # 2. Dell XPS 15 9530 Core i7
    try:
        p_dell = Product.objects.get(sku='DELL-XPS15-I7')
        p_dell.specifications = {
            "Màn hình": "15.6 inch FHD+ (1920 x 1200) InfinityEdge, IPS, 500 nits",
            "Hệ điều hành": "Windows 11 Home",
            "CPU": "Intel Core i7-13700H (14 Cores, 20 Threads, up to 5.0 GHz)",
            "RAM": "16GB LPDDR5 4800MHz",
            "SSD": "512GB PCIe NVMe M.2 SSD",
            "Card màn hình": "NVIDIA GeForce RTX 4060 8GB GDDR6",
            "Trọng lượng": "1.92 kg",
            "Pin": "86 Whr, 6-cell Lithium-ion"
        }
        p_dell.save()
        print(f"[Updated specifications] {p_dell.name}")

        # Delete existing variants if any
        ProductVariant.objects.filter(product=p_dell).delete()

        # Create Variants
        v1 = ProductVariant.objects.create(
            product=p_dell,
            name="Dell XPS 15 9530 - RAM 16GB, SSD 512GB",
            sku="DELL-XPS15-I7-16-512",
            price=Decimal("42990000"),
            stock_quantity=5,
            attributes={"ram": "16GB", "ssd": "512GB", "color": "Silver"},
            is_active=True
        )
        v2 = ProductVariant.objects.create(
            product=p_dell,
            name="Dell XPS 15 9530 - RAM 32GB, SSD 1TB",
            sku="DELL-XPS15-I7-32-1TB",
            price=Decimal("46990000"),
            stock_quantity=10,
            attributes={"ram": "32GB", "ssd": "1TB", "color": "Silver"},
            is_active=True
        )
        print(f"  Created variants: {v1.sku}, {v2.sku}")
    except Product.DoesNotExist:
        print("  [ERROR] Dell XPS 15 not found in DB")

    # 3. Giày Sneaker Nam Nike Air Max 270
    try:
        p_nike = Product.objects.get(sku='NIKE-AM270-NAM')
        p_nike.specifications = {
            "Loại sản phẩm": "Giày Sneaker",
            "Phân khúc": "Chạy bộ / Thời trang Streetwear",
            "Chất liệu upper": "Mesh (Lưới dệt thoáng khí) kết hợp với các miếng phủ tổng hợp",
            "Công nghệ đế": "Đệm khí Air Max gót chân 270 độ lớn nhất, đế giữa bọt khí xốp êm ái",
            "Chất liệu đế ngoài": "Cao su lưu hóa chống mòn chống trượt",
            "Kiểu khóa": "Thắt dây (Lace-up)"
        }
        p_nike.save()
        print(f"[Updated specifications] {p_nike.name}")

        # Delete existing variants if any
        ProductVariant.objects.filter(product=p_nike).delete()

        # Create Variants
        v1 = ProductVariant.objects.create(
            product=p_nike,
            name="Nike Air Max 270 - Màu Đen - Size 42",
            sku="NIKE-AM270-NAM-BLK-42",
            price=Decimal("3290000"),
            stock_quantity=20,
            attributes={"color": "Đen", "size": "42"},
            is_active=True
        )
        v2 = ProductVariant.objects.create(
            product=p_nike,
            name="Nike Air Max 270 - Màu Đen - Size 43",
            sku="NIKE-AM270-NAM-BLK-43",
            price=Decimal("3290000"),
            stock_quantity=15,
            attributes={"color": "Đen", "size": "43"},
            is_active=True
        )
        v3 = ProductVariant.objects.create(
            product=p_nike,
            name="Nike Air Max 270 - Màu Trắng - Size 42",
            sku="NIKE-AM270-NAM-WHT-42",
            price=Decimal("3290000"),
            stock_quantity=10,
            attributes={"color": "Trắng", "size": "42"},
            is_active=True
        )
        print(f"  Created variants: {v1.sku}, {v2.sku}, {v3.sku}")
    except Product.DoesNotExist:
        print("  [ERROR] Nike Air Max 270 not found in DB")

    print("\nSeeding of specifications and variants completed successfully!")
    print("=" * 60)
    
    import time
    print("Waiting 5 seconds for background notification threads to complete...")
    time.sleep(5)
    print("Done!")

if __name__ == '__main__':
    run()
