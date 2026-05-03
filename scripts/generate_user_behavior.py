"""
Script sinh dữ liệu User Behavior Data cho AI Service
Yêu cầu: 500 users + 8 behaviors

Behaviors:
1. view - Xem sản phẩm
2. click - Click vào sản phẩm
3. add_to_cart - Thêm vào giỏ hàng
4. purchase - Mua hàng
5. wishlist - Thêm vào wishlist
6. search - Tìm kiếm
7. review - Đánh giá sản phẩm
8. share - Chia sẻ sản phẩm
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# Seed for reproducibility
random.seed(42)
np.random.seed(42)

# Constants
NUM_USERS = 500
NUM_PRODUCTS = 100
NUM_CATEGORIES = 10

# 8 Behaviors với trọng số xác suất
ACTIONS = [
    'view',         # Xem sản phẩm - phổ biến nhất
    'click',        # Click chi tiết
    'add_to_cart',  # Thêm giỏ hàng
    'purchase',     # Mua hàng
    'wishlist',     # Yêu thích
    'search',       # Tìm kiếm
    'review',       # Đánh giá
    'share'         # Chia sẻ
]

# Trọng số cho mỗi action (tổng = 1.0)
ACTION_WEIGHTS = [0.30, 0.25, 0.15, 0.10, 0.07, 0.06, 0.04, 0.03]

# Product categories
CATEGORIES = [
    'Điện thoại', 'Laptop', 'Máy tính bảng', 'Phụ kiện', 'Đồng hồ',
    'Thời trang', 'Gia dụng', 'Sách', 'Thể thao', 'Mỹ phẩm'
]

# Brands
BRANDS = [
    'Apple', 'Samsung', 'Xiaomi', 'Sony', 'LG',
    'Dell', 'HP', 'Asus', 'Lenovo', 'Acer'
]


def generate_products(num_products=NUM_PRODUCTS):
    """Sinh danh sách sản phẩm"""
    products = []
    for i in range(1, num_products + 1):
        category = random.choice(CATEGORIES)
        brand = random.choice(BRANDS)
        price = random.randint(100000, 50000000)

        products.append({
            'product_id': f'P{i:04d}',
            'name': f'{brand} {category} Model {i}',
            'category': category,
            'brand': brand,
            'price': price
        })

    return pd.DataFrame(products)


def generate_user_behavior(num_users=NUM_USERS, num_products=NUM_PRODUCTS):
    """
    Sinh dữ liệu hành vi người dùng

    Output columns:
    - user_id: ID người dùng (U0001 - U0500)
    - product_id: ID sản phẩm (P0001 - P0100)
    - action: Loại hành vi (8 loại)
    - timestamp: Thời gian hành vi
    - session_id: ID phiên làm việc
    - device: Thiết bị (mobile, desktop, tablet)
    - duration: Thời gian tương tác (giây)
    """

    data = []
    base_time = datetime.now() - timedelta(days=90)
    devices = ['mobile', 'desktop', 'tablet']
    device_weights = [0.6, 0.3, 0.1]

    print(f"Generating behavior data for {num_users} users...")

    for user_idx in range(1, num_users + 1):
        user_id = f'U{user_idx:04d}'

        # Mỗi user có số interactions khác nhau (phân phối Poisson)
        num_interactions = max(10, int(np.random.poisson(30)))

        # User preferences - mỗi user có xu hướng thích một số categories
        preferred_categories = random.sample(CATEGORIES, k=random.randint(2, 4))

        # Session tracking
        current_session = 1
        last_action_time = None

        for _ in range(num_interactions):
            # Random timestamp trong 90 ngày
            days_offset = random.randint(0, 89)
            hours_offset = random.randint(0, 23)
            mins_offset = random.randint(0, 59)
            secs_offset = random.randint(0, 59)

            timestamp = base_time + timedelta(
                days=days_offset,
                hours=hours_offset,
                minutes=mins_offset,
                seconds=secs_offset
            )

            # New session if gap > 30 minutes
            if last_action_time and (timestamp - last_action_time).seconds > 1800:
                current_session += 1
            last_action_time = timestamp

            # Product selection - bias toward preferred categories
            if random.random() < 0.7:  # 70% chance to pick from preferred
                # Pick product from preferred category
                product_idx = random.randint(1, num_products)
            else:
                product_idx = random.randint(1, num_products)

            product_id = f'P{product_idx:04d}'

            # Action selection with weights
            action = random.choices(ACTIONS, weights=ACTION_WEIGHTS)[0]

            # Device selection
            device = random.choices(devices, weights=device_weights)[0]

            # Duration based on action type
            if action == 'view':
                duration = random.randint(5, 120)
            elif action == 'click':
                duration = random.randint(10, 300)
            elif action == 'search':
                duration = random.randint(3, 30)
            elif action == 'review':
                duration = random.randint(60, 600)
            else:
                duration = random.randint(5, 60)

            data.append({
                'user_id': user_id,
                'product_id': product_id,
                'action': action,
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'session_id': f'{user_id}_S{current_session:03d}',
                'device': device,
                'duration': duration
            })

        if user_idx % 100 == 0:
            print(f"  Processed {user_idx}/{num_users} users...")

    # Create DataFrame and sort by timestamp
    df = pd.DataFrame(data)
    df = df.sort_values('timestamp').reset_index(drop=True)

    return df


def analyze_data(df):
    """Phân tích và in thống kê dữ liệu"""
    print("\n" + "="*60)
    print("THỐNG KÊ DỮ LIỆU USER BEHAVIOR")
    print("="*60)

    print(f"\nTổng số records: {len(df):,}")
    print(f"Số users: {df['user_id'].nunique()}")
    print(f"Số products: {df['product_id'].nunique()}")
    print(f"Số sessions: {df['session_id'].nunique()}")

    print(f"\nThời gian: {df['timestamp'].min()} đến {df['timestamp'].max()}")

    print("\n--- Phân bố Actions (8 behaviors) ---")
    action_counts = df['action'].value_counts()
    for action in ACTIONS:
        count = action_counts.get(action, 0)
        pct = count / len(df) * 100
        bar = '█' * int(pct / 2)
        print(f"  {action:12s}: {count:6,} ({pct:5.2f}%) {bar}")

    print("\n--- Phân bố Devices ---")
    device_counts = df['device'].value_counts()
    for device, count in device_counts.items():
        pct = count / len(df) * 100
        print(f"  {device:10s}: {count:6,} ({pct:5.2f}%)")

    print("\n--- Top 10 Products (theo interactions) ---")
    top_products = df['product_id'].value_counts().head(10)
    for i, (product, count) in enumerate(top_products.items(), 1):
        print(f"  {i:2d}. {product}: {count:,} interactions")

    print("\n--- Top 10 Users (theo interactions) ---")
    top_users = df['user_id'].value_counts().head(10)
    for i, (user, count) in enumerate(top_users.items(), 1):
        print(f"  {i:2d}. {user}: {count:,} interactions")

    print("\n--- Sample Data (20 dòng đầu) ---")
    print(df.head(20).to_string(index=False))


def main():
    # Output directory
    output_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(output_dir), 'data')

    # Create data directory if not exists
    os.makedirs(data_dir, exist_ok=True)

    # Generate products
    print("Generating products...")
    products_df = generate_products()
    products_file = os.path.join(data_dir, 'products.csv')
    products_df.to_csv(products_file, index=False)
    print(f"Saved {len(products_df)} products to {products_file}")

    # Generate user behavior data
    print("\nGenerating user behavior data...")
    behavior_df = generate_user_behavior()

    # Save to CSV
    output_file = os.path.join(data_dir, 'data_user500.csv')
    behavior_df.to_csv(output_file, index=False)
    print(f"\nSaved to: {output_file}")

    # Also save to scripts folder for easy access
    output_file_scripts = os.path.join(output_dir, 'data_user500.csv')
    behavior_df.to_csv(output_file_scripts, index=False)
    print(f"Also saved to: {output_file_scripts}")

    # Analyze and print statistics
    analyze_data(behavior_df)

    print("\n" + "="*60)
    print("HOÀN THÀNH!")
    print("="*60)
    print(f"\nFiles created:")
    print(f"  1. {output_file}")
    print(f"  2. {products_file}")
    print(f"\nData format:")
    print(f"  - {len(behavior_df):,} records")
    print(f"  - {behavior_df['user_id'].nunique()} users")
    print(f"  - 8 behavior types: {', '.join(ACTIONS)}")


if __name__ == '__main__':
    main()
