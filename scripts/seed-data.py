#!/usr/bin/env python
"""
Script tạo dữ liệu mẫu cho hệ thống AI-Ecommerce
Chạy: python scripts/seed-data.py
"""

import os
import sys
import django
import uuid
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gateway.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'api-gateway'))

# Sample data
CATEGORIES = [
    {'name': 'Điện thoại & Phụ kiện', 'slug': 'dien-thoai-phu-kien'},
    {'name': 'Máy tính & Laptop', 'slug': 'may-tinh-laptop'},
    {'name': 'Thời trang Nam', 'slug': 'thoi-trang-nam'},
    {'name': 'Thời trang Nữ', 'slug': 'thoi-trang-nu'},
    {'name': 'Đồ gia dụng', 'slug': 'do-gia-dung'},
    {'name': 'Sách & Văn phòng phẩm', 'slug': 'sach-van-phong-pham'},
]

PRODUCTS = [
    {
        'name': 'iPhone 15 Pro Max 256GB',
        'slug': 'iphone-15-pro-max-256gb',
        'price': 29990000,
        'compare_price': 34990000,
        'brand': 'Apple',
        'description': 'iPhone 15 Pro Max với chip A17 Pro, camera 48MP, màn hình 6.7 inch Super Retina XDR.',
        'category_slug': 'dien-thoai-phu-kien',
    },
    {
        'name': 'Samsung Galaxy S24 Ultra',
        'slug': 'samsung-galaxy-s24-ultra',
        'price': 27990000,
        'compare_price': 31990000,
        'brand': 'Samsung',
        'description': 'Galaxy S24 Ultra với Galaxy AI, camera 200MP, S Pen tích hợp.',
        'category_slug': 'dien-thoai-phu-kien',
    },
    {
        'name': 'MacBook Pro 14" M3 Pro',
        'slug': 'macbook-pro-14-m3-pro',
        'price': 49990000,
        'compare_price': 54990000,
        'brand': 'Apple',
        'description': 'MacBook Pro 14 inch với chip M3 Pro, RAM 18GB, SSD 512GB.',
        'category_slug': 'may-tinh-laptop',
    },
    {
        'name': 'Áo thun nam basic cotton',
        'slug': 'ao-thun-nam-basic-cotton',
        'price': 199000,
        'compare_price': 299000,
        'brand': 'Local Brand',
        'description': 'Áo thun nam chất liệu cotton 100%, thoáng mát, nhiều màu sắc.',
        'category_slug': 'thoi-trang-nam',
    },
    {
        'name': 'Váy đầm công sở nữ',
        'slug': 'vay-dam-cong-so-nu',
        'price': 450000,
        'compare_price': 599000,
        'brand': 'Fashion Brand',
        'description': 'Váy đầm công sở thanh lịch, chất liệu cao cấp, form dáng đẹp.',
        'category_slug': 'thoi-trang-nu',
    },
    {
        'name': 'Nồi chiên không dầu 5L',
        'slug': 'noi-chien-khong-dau-5l',
        'price': 1990000,
        'compare_price': 2500000,
        'brand': 'Philips',
        'description': 'Nồi chiên không dầu dung tích 5L, công suất 1400W, nhiều chế độ nấu.',
        'category_slug': 'do-gia-dung',
    },
]

USERS = [
    {
        'email': 'admin@example.com',
        'password': 'admin123',
        'role': 'admin',
        'is_staff': True,
        'is_superuser': True,
    },
    {
        'email': 'user@example.com',
        'password': 'user123',
        'role': 'customer',
    },
    {
        'email': 'seller@example.com',
        'password': 'seller123',
        'role': 'seller',
    },
]


def main():
    print("=" * 50)
    print("AI-Ecommerce Seed Data Script")
    print("=" * 50)
    print()
    print("Dữ liệu mẫu đã được định nghĩa:")
    print(f"- {len(CATEGORIES)} danh mục")
    print(f"- {len(PRODUCTS)} sản phẩm")
    print(f"- {len(USERS)} người dùng")
    print()
    print("Để seed dữ liệu, chạy lệnh sau trong từng service:")
    print()
    print("1. Auth Service - Tạo users:")
    print("   docker-compose exec auth-service python manage.py shell")
    print()
    print("2. Product Service - Tạo categories và products:")
    print("   docker-compose exec product-service python manage.py shell")
    print()
    print("Hoặc sử dụng Django fixtures:")
    print("   python manage.py loaddata fixtures/initial_data.json")
    print()


if __name__ == '__main__':
    main()
