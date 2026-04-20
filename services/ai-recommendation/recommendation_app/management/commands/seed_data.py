"""
Seed Data cho AI Recommendation Service
Tạo dữ liệu mẫu với 10 users và các interactions
"""

import uuid
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from recommendation_app.models import UserInteraction, ProductSimilarity, UserRecommendation


class Command(BaseCommand):
    help = 'Seed sample data for AI Recommendation testing'

    # 10 Sample Users
    USERS = [
        {'id': uuid.UUID('11111111-1111-1111-1111-111111111111'), 'name': 'Nguyen Van A', 'type': 'tech_lover'},
        {'id': uuid.UUID('22222222-2222-2222-2222-222222222222'), 'name': 'Tran Thi B', 'type': 'fashionista'},
        {'id': uuid.UUID('33333333-3333-3333-3333-333333333333'), 'name': 'Le Van C', 'type': 'gamer'},
        {'id': uuid.UUID('44444444-4444-4444-4444-444444444444'), 'name': 'Pham Thi D', 'type': 'home_maker'},
        {'id': uuid.UUID('55555555-5555-5555-5555-555555555555'), 'name': 'Hoang Van E', 'type': 'sports_fan'},
        {'id': uuid.UUID('66666666-6666-6666-6666-666666666666'), 'name': 'Nguyen Thi F', 'type': 'bookworm'},
        {'id': uuid.UUID('77777777-7777-7777-7777-777777777777'), 'name': 'Tran Van G', 'type': 'tech_lover'},
        {'id': uuid.UUID('88888888-8888-8888-8888-888888888888'), 'name': 'Le Thi H', 'type': 'fashionista'},
        {'id': uuid.UUID('99999999-9999-9999-9999-999999999999'), 'name': 'Pham Van I', 'type': 'gamer'},
        {'id': uuid.UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'), 'name': 'Hoang Thi K', 'type': 'home_maker'},
    ]

    # Sample Products by Category
    PRODUCTS = {
        'electronics': [
            {'id': uuid.UUID('e1111111-1111-1111-1111-111111111111'), 'name': 'iPhone 15 Pro Max', 'price': 34990000, 'brand': 'Apple'},
            {'id': uuid.UUID('e2222222-2222-2222-2222-222222222222'), 'name': 'Samsung Galaxy S24 Ultra', 'price': 31990000, 'brand': 'Samsung'},
            {'id': uuid.UUID('e3333333-3333-3333-3333-333333333333'), 'name': 'MacBook Pro M3', 'price': 49990000, 'brand': 'Apple'},
            {'id': uuid.UUID('e4444444-4444-4444-4444-444444444444'), 'name': 'Dell XPS 15', 'price': 35990000, 'brand': 'Dell'},
            {'id': uuid.UUID('e5555555-5555-5555-5555-555555555555'), 'name': 'iPad Pro 12.9', 'price': 28990000, 'brand': 'Apple'},
            {'id': uuid.UUID('e6666666-6666-6666-6666-666666666666'), 'name': 'AirPods Pro 2', 'price': 6490000, 'brand': 'Apple'},
            {'id': uuid.UUID('e7777777-7777-7777-7777-777777777777'), 'name': 'Sony WH-1000XM5', 'price': 8490000, 'brand': 'Sony'},
            {'id': uuid.UUID('e8888888-8888-8888-8888-888888888888'), 'name': 'Apple Watch Ultra 2', 'price': 21990000, 'brand': 'Apple'},
        ],
        'gaming': [
            {'id': uuid.UUID('g1111111-1111-1111-1111-111111111111'), 'name': 'PlayStation 5', 'price': 14990000, 'brand': 'Sony'},
            {'id': uuid.UUID('g2222222-2222-2222-2222-222222222222'), 'name': 'Xbox Series X', 'price': 13990000, 'brand': 'Microsoft'},
            {'id': uuid.UUID('g3333333-3333-3333-3333-333333333333'), 'name': 'Nintendo Switch OLED', 'price': 8990000, 'brand': 'Nintendo'},
            {'id': uuid.UUID('g4444444-4444-4444-4444-444444444444'), 'name': 'Gaming Chair Razer', 'price': 12990000, 'brand': 'Razer'},
            {'id': uuid.UUID('g5555555-5555-5555-5555-555555555555'), 'name': 'Logitech G Pro X', 'price': 3290000, 'brand': 'Logitech'},
            {'id': uuid.UUID('g6666666-6666-6666-6666-666666666666'), 'name': 'Razer DeathAdder V3', 'price': 1990000, 'brand': 'Razer'},
            {'id': uuid.UUID('g7777777-7777-7777-7777-777777777777'), 'name': 'ASUS ROG Swift 27"', 'price': 15990000, 'brand': 'ASUS'},
        ],
        'fashion': [
            {'id': uuid.UUID('f1111111-1111-1111-1111-111111111111'), 'name': 'Áo thun Uniqlo', 'price': 399000, 'brand': 'Uniqlo'},
            {'id': uuid.UUID('f2222222-2222-2222-2222-222222222222'), 'name': 'Quần jeans Levis 501', 'price': 1890000, 'brand': 'Levis'},
            {'id': uuid.UUID('f3333333-3333-3333-3333-333333333333'), 'name': 'Giày Nike Air Max', 'price': 3990000, 'brand': 'Nike'},
            {'id': uuid.UUID('f4444444-4444-4444-4444-444444444444'), 'name': 'Túi xách Coach', 'price': 8990000, 'brand': 'Coach'},
            {'id': uuid.UUID('f5555555-5555-5555-5555-555555555555'), 'name': 'Đồng hồ Casio', 'price': 2490000, 'brand': 'Casio'},
            {'id': uuid.UUID('f6666666-6666-6666-6666-666666666666'), 'name': 'Kính mát Ray-Ban', 'price': 3990000, 'brand': 'Ray-Ban'},
            {'id': uuid.UUID('f7777777-7777-7777-7777-777777777777'), 'name': 'Váy đầm Zara', 'price': 1290000, 'brand': 'Zara'},
            {'id': uuid.UUID('f8888888-8888-8888-8888-888888888888'), 'name': 'Áo khoác H&M', 'price': 899000, 'brand': 'H&M'},
        ],
        'home': [
            {'id': uuid.UUID('h1111111-1111-1111-1111-111111111111'), 'name': 'Nồi chiên không dầu Philips', 'price': 3490000, 'brand': 'Philips'},
            {'id': uuid.UUID('h2222222-2222-2222-2222-222222222222'), 'name': 'Máy hút bụi Dyson V15', 'price': 18990000, 'brand': 'Dyson'},
            {'id': uuid.UUID('h3333333-3333-3333-3333-333333333333'), 'name': 'Nồi cơm điện Cuckoo', 'price': 4990000, 'brand': 'Cuckoo'},
            {'id': uuid.UUID('h4444444-4444-4444-4444-444444444444'), 'name': 'Máy lọc không khí Xiaomi', 'price': 2990000, 'brand': 'Xiaomi'},
            {'id': uuid.UUID('h5555555-5555-5555-5555-555555555555'), 'name': 'Bàn làm việc IKEA', 'price': 3490000, 'brand': 'IKEA'},
            {'id': uuid.UUID('h6666666-6666-6666-6666-666666666666'), 'name': 'Ghế công thái học', 'price': 5990000, 'brand': 'ErgoChair'},
        ],
        'sports': [
            {'id': uuid.UUID('s1111111-1111-1111-1111-111111111111'), 'name': 'Giày chạy bộ Adidas', 'price': 2990000, 'brand': 'Adidas'},
            {'id': uuid.UUID('s2222222-2222-2222-2222-222222222222'), 'name': 'Vợt cầu lông Yonex', 'price': 1890000, 'brand': 'Yonex'},
            {'id': uuid.UUID('s3333333-3333-3333-3333-333333333333'), 'name': 'Bóng đá Nike', 'price': 890000, 'brand': 'Nike'},
            {'id': uuid.UUID('s4444444-4444-4444-4444-444444444444'), 'name': 'Máy chạy bộ Elip', 'price': 15990000, 'brand': 'Elip'},
            {'id': uuid.UUID('s5555555-5555-5555-5555-555555555555'), 'name': 'Tạ tay 10kg', 'price': 590000, 'brand': 'Generic'},
            {'id': uuid.UUID('s6666666-6666-6666-6666-666666666666'), 'name': 'Thảm yoga', 'price': 390000, 'brand': 'Generic'},
        ],
        'books': [
            {'id': uuid.UUID('b1111111-1111-1111-1111-111111111111'), 'name': 'Đắc Nhân Tâm', 'price': 86000, 'brand': 'NXB Tổng hợp'},
            {'id': uuid.UUID('b2222222-2222-2222-2222-222222222222'), 'name': 'Nhà Giả Kim', 'price': 79000, 'brand': 'NXB Hội Nhà Văn'},
            {'id': uuid.UUID('b3333333-3333-3333-3333-333333333333'), 'name': 'Tư Duy Nhanh Và Chậm', 'price': 199000, 'brand': 'NXB Thế Giới'},
            {'id': uuid.UUID('b4444444-4444-4444-4444-444444444444'), 'name': 'Atomic Habits', 'price': 159000, 'brand': 'NXB Lao Động'},
            {'id': uuid.UUID('b5555555-5555-5555-5555-555555555555'), 'name': 'Sapiens - Lược Sử Loài Người', 'price': 209000, 'brand': 'NXB Tri Thức'},
        ],
    }

    # User preferences mapping
    USER_PREFERENCES = {
        'tech_lover': ['electronics', 'gaming'],
        'fashionista': ['fashion'],
        'gamer': ['gaming', 'electronics'],
        'home_maker': ['home', 'electronics'],
        'sports_fan': ['sports', 'fashion'],
        'bookworm': ['books', 'home'],
    }

    def handle(self, *args, **options):
        self.stdout.write('Seeding AI Recommendation data...')

        # Clear existing data
        UserInteraction.objects.all().delete()
        ProductSimilarity.objects.all().delete()
        UserRecommendation.objects.all().delete()

        # Get all products flat list
        all_products = []
        for category, products in self.PRODUCTS.items():
            for p in products:
                p['category'] = category
                all_products.append(p)

        # Generate interactions for each user
        interactions_created = 0
        now = timezone.now()

        for user in self.USERS:
            user_type = user['type']
            preferred_categories = self.USER_PREFERENCES.get(user_type, ['electronics'])

            # Get products from preferred categories
            preferred_products = [p for p in all_products if p['category'] in preferred_categories]
            other_products = [p for p in all_products if p['category'] not in preferred_categories]

            # Generate behavior sequence (15-30 interactions per user)
            num_interactions = random.randint(15, 30)

            for i in range(num_interactions):
                # 80% preferred, 20% other
                if random.random() < 0.8 and preferred_products:
                    product = random.choice(preferred_products)
                else:
                    product = random.choice(other_products) if other_products else random.choice(all_products)

                # Determine interaction type based on position in sequence
                # Earlier = more views, later = more purchases
                progress = i / num_interactions
                rand = random.random()

                if progress < 0.3:
                    # Early stage: mostly views
                    if rand < 0.7:
                        interaction_type = 'view'
                    elif rand < 0.9:
                        interaction_type = 'cart'
                    else:
                        interaction_type = 'wishlist'
                elif progress < 0.7:
                    # Middle stage: mixed
                    if rand < 0.4:
                        interaction_type = 'view'
                    elif rand < 0.7:
                        interaction_type = 'cart'
                    elif rand < 0.85:
                        interaction_type = 'wishlist'
                    else:
                        interaction_type = 'purchase'
                else:
                    # Late stage: purchases and reviews
                    if rand < 0.2:
                        interaction_type = 'view'
                    elif rand < 0.4:
                        interaction_type = 'cart'
                    elif rand < 0.7:
                        interaction_type = 'purchase'
                    else:
                        interaction_type = 'review'

                # Random timestamp within last 30 days
                days_ago = random.randint(0, 30)
                hours_ago = random.randint(0, 23)
                timestamp = now - timedelta(days=days_ago, hours=hours_ago, minutes=random.randint(0, 59))

                # Create interaction
                UserInteraction.objects.create(
                    user_id=user['id'],
                    product_id=product['id'],
                    interaction_type=interaction_type,
                    score=random.uniform(0.5, 1.0) if interaction_type != 'view' else 1.0,
                    created_at=timestamp
                )
                interactions_created += 1

        self.stdout.write(f'Created {interactions_created} user interactions')

        # Generate product similarities
        similarities_created = 0
        for category, products in self.PRODUCTS.items():
            for i, p1 in enumerate(products):
                for j, p2 in enumerate(products):
                    if i != j:
                        # Same category = higher similarity
                        score = random.uniform(0.6, 0.95)
                        ProductSimilarity.objects.create(
                            product_id=p1['id'],
                            similar_product_id=p2['id'],
                            similarity_score=score
                        )
                        similarities_created += 1

        # Cross-category similarities (lower scores)
        categories = list(self.PRODUCTS.keys())
        for i, cat1 in enumerate(categories):
            for cat2 in categories[i+1:]:
                # Pick 2-3 random products from each category
                products1 = random.sample(self.PRODUCTS[cat1], min(2, len(self.PRODUCTS[cat1])))
                products2 = random.sample(self.PRODUCTS[cat2], min(2, len(self.PRODUCTS[cat2])))

                for p1 in products1:
                    for p2 in products2:
                        score = random.uniform(0.1, 0.4)
                        ProductSimilarity.objects.create(
                            product_id=p1['id'],
                            similar_product_id=p2['id'],
                            similarity_score=score
                        )
                        similarities_created += 1

        self.stdout.write(f'Created {similarities_created} product similarities')

        # Summary
        self.stdout.write(self.style.SUCCESS(f'''
=== Seed Data Summary ===
Users: {len(self.USERS)}
Products: {len(all_products)}
User Interactions: {interactions_created}
Product Similarities: {similarities_created}

User IDs for testing:
'''))
        for user in self.USERS:
            self.stdout.write(f"  - {user['name']} ({user['type']}): {user['id']}")

        self.stdout.write(self.style.SUCCESS('\nSeed data created successfully!'))
