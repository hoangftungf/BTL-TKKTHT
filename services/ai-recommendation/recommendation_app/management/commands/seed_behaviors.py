"""
Seed User Behaviors for AI Pipeline
Creates 10,000-20,000 realistic user behaviors

Requirements:
- Each user: 20-50 interactions
- Action distribution: view 60%, cart 20%, purchase 10%, search 10%
- Realistic funnel: view -> cart -> purchase
- Timeline simulation with proper timestamps
"""

import uuid
import random
import logging
from datetime import timedelta
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import connection

from recommendation_app.models import UserBehavior

logger = logging.getLogger(__name__)

# Seed for reproducibility
random.seed(42)


class Command(BaseCommand):
    help = 'Seed realistic user behaviors for AI pipeline'

    # Action distribution weights (8 core actions)
    ACTION_WEIGHTS = {
        'view_product': 0.35,
        'click_product': 0.20,
        'add_to_cart': 0.12,
        'remove_from_cart': 0.03,
        'purchase': 0.08,
        'add_to_wishlist': 0.07,
        'search': 0.10,
        'view_category': 0.05,
    }

    # Search queries for variety
    SEARCH_QUERIES = [
        'điện thoại samsung', 'iphone 15', 'laptop gaming', 'tai nghe bluetooth',
        'áo thun nam', 'giày thể thao', 'đồng hồ thông minh', 'máy tính bảng',
        'nồi chiên không dầu', 'robot hút bụi', 'sách hay', 'quần jean',
        'bàn phím cơ', 'chuột gaming', 'màn hình 27 inch', 'loa bluetooth',
        'đèn bàn học', 'ghế công thái học', 'balo laptop', 'ổ cứng ssd',
        'camera an ninh', 'máy lọc không khí', 'tủ lạnh mini', 'quạt điều hòa',
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-interactions',
            type=int,
            default=20,
            help='Minimum interactions per user (default: 20)'
        )
        parser.add_argument(
            '--max-interactions',
            type=int,
            default=50,
            help='Maximum interactions per user (default: 50)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing behaviors before seeding'
        )

    def handle(self, *args, **options):
        min_interactions = options['min_interactions']
        max_interactions = options['max_interactions']
        clear_existing = options['clear']

        self.stdout.write('Starting behavior seeding...')

        if clear_existing:
            count = UserBehavior.objects.count()
            UserBehavior.objects.all().delete()
            self.stdout.write(f'Cleared {count} existing behaviors')

        # Fetch users and products
        users = self._get_users()
        products = self._get_products()

        if not users:
            self.stdout.write(self.style.ERROR(
                'No users found! Run seed_users first.'
            ))
            return

        if not products:
            self.stdout.write(self.style.ERROR(
                'No products found! Ensure product-service has data.'
            ))
            return

        self.stdout.write(f'Found {len(users)} users and {len(products)} products')

        # Group products by category for realistic behavior
        products_by_category = defaultdict(list)
        for p in products:
            cat = p.get('category_name', 'unknown')
            products_by_category[cat].append(p)

        # Generate behaviors
        behaviors = []
        total_behaviors = 0
        base_time = timezone.now() - timedelta(days=90)

        for idx, user_id in enumerate(users):
            num_interactions = random.randint(min_interactions, max_interactions)

            # User state tracking for realistic funnel
            user_viewed = []  # Products user has viewed
            user_carted = []  # Products in cart

            # Each user has preferred categories (2-3)
            categories = list(products_by_category.keys())
            if categories:
                preferred_cats = random.sample(
                    categories, min(random.randint(2, 3), len(categories))
                )
            else:
                preferred_cats = []

            # Generate timeline of actions
            user_behaviors = []
            user_wishlisted = []  # Track wishlist items
            current_time = base_time + timedelta(days=random.randint(0, 30))

            for i in range(num_interactions):
                # Progress through time
                current_time += timedelta(
                    hours=random.randint(1, 48),
                    minutes=random.randint(0, 59)
                )

                # Don't exceed current time
                if current_time > timezone.now():
                    current_time = timezone.now() - timedelta(minutes=random.randint(1, 60))

                # Choose action based on weights and funnel logic
                action = self._choose_action(user_viewed, user_carted, user_wishlisted)

                # Choose product/category based on action type
                product_id = None
                category_id = None
                search_query = None

                if action == 'search':
                    # Search can be with or without product
                    search_query = random.choice(self.SEARCH_QUERIES)
                    if random.random() < 0.3:  # 30% search leads to product view
                        product_id = self._pick_product(products, preferred_cats, products_by_category)
                        if product_id:
                            user_viewed.append(product_id)

                elif action == 'view_product':
                    product_id = self._pick_product(products, preferred_cats, products_by_category)
                    if product_id:
                        user_viewed.append(product_id)

                elif action == 'click_product':
                    # Click from product list (before full view)
                    product_id = self._pick_product(products, preferred_cats, products_by_category)

                elif action == 'view_category':
                    # View category page
                    if preferred_cats:
                        # Pick a category from preferred
                        cat_name = random.choice(preferred_cats)
                        # Get a product from this category to extract category_id
                        if products_by_category.get(cat_name):
                            p = random.choice(products_by_category[cat_name])
                            # Generate a consistent category UUID from category name
                            category_id = uuid.uuid5(uuid.NAMESPACE_DNS, f'category_{cat_name}@ecommerce.local')

                elif action == 'add_to_cart':
                    # Cart should be from viewed products (realistic funnel)
                    if user_viewed:
                        product_id = random.choice(user_viewed)
                        user_carted.append(product_id)
                    else:
                        # Fallback: view first then cart
                        product_id = self._pick_product(products, preferred_cats, products_by_category)
                        if product_id:
                            user_viewed.append(product_id)
                            user_carted.append(product_id)

                elif action == 'remove_from_cart':
                    # Remove from cart (user changed mind)
                    if user_carted:
                        product_id = random.choice(user_carted)
                        user_carted.remove(product_id)
                    else:
                        # Skip if no cart items
                        continue

                elif action == 'add_to_wishlist':
                    # Add to wishlist from viewed products
                    if user_viewed:
                        product_id = random.choice(user_viewed)
                        if product_id not in user_wishlisted:
                            user_wishlisted.append(product_id)
                    else:
                        product_id = self._pick_product(products, preferred_cats, products_by_category)
                        if product_id:
                            user_wishlisted.append(product_id)

                elif action == 'purchase':
                    # Purchase from cart (realistic funnel)
                    if user_carted:
                        product_id = random.choice(user_carted)
                        user_carted.remove(product_id)  # Remove from cart after purchase
                    elif user_viewed:
                        # Direct purchase from viewed
                        product_id = random.choice(user_viewed)
                    else:
                        # Impulse buy (rare)
                        product_id = self._pick_product(products, preferred_cats, products_by_category)

                # Create behavior record
                behavior = UserBehavior(
                    user_id=user_id,
                    product_id=product_id,
                    category_id=category_id,
                    action=action,
                    search_query=search_query,
                    created_at=current_time
                )
                user_behaviors.append(behavior)

            # Sort by timestamp
            user_behaviors.sort(key=lambda x: x.created_at)
            behaviors.extend(user_behaviors)
            total_behaviors += len(user_behaviors)

            if (idx + 1) % 50 == 0:
                self.stdout.write(f'  Generated behaviors for {idx + 1}/{len(users)} users...')

            # Batch insert every 500 users to avoid memory issues
            if len(behaviors) >= 5000:
                UserBehavior.objects.bulk_create(behaviors, batch_size=500)
                self.stdout.write(f'  Inserted {len(behaviors)} behaviors...')
                behaviors = []

        # Insert remaining behaviors
        if behaviors:
            UserBehavior.objects.bulk_create(behaviors, batch_size=500)
            self.stdout.write(f'  Inserted {len(behaviors)} behaviors...')

        # Print statistics
        self._print_statistics(total_behaviors)

    def _get_users(self):
        """Get user IDs from ai_users table"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id FROM ai_users ORDER BY username")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            return []

    def _get_products(self):
        """
        Get products from product service or use existing data
        For local testing, we create sample products
        """
        import httpx
        import os

        product_service_url = os.environ.get(
            'PRODUCT_SERVICE_URL', 'http://product-service:8003'
        )

        # Try multiple endpoints
        endpoints = [
            f"{product_service_url}/",
            f"{product_service_url}/api/products/",
        ]

        for endpoint in endpoints:
            try:
                response = httpx.get(
                    endpoint,
                    params={'page_size': 1000},
                    timeout=30.0
                )
                if response.status_code == 200:
                    data = response.json()
                    products = data.get('results', [])
                    if products:
                        self.stdout.write(f'  Fetched {len(products)} products from {endpoint}')
                        return [
                            {
                                'id': p['id'],
                                'name': p.get('name', ''),
                                'category_name': p.get('category_name', 'unknown') or 'unknown'
                            }
                            for p in products
                        ]
            except Exception as e:
                logger.warning(f"Could not fetch from {endpoint}: {e}")

        # Fallback: create sample product UUIDs
        self.stdout.write('  Using sample product data...')
        return self._generate_sample_products()

    def _generate_sample_products(self):
        """Generate sample products for testing"""
        categories = [
            'Điện thoại', 'Laptop', 'Máy tính bảng', 'Phụ kiện',
            'Thời trang nam', 'Thời trang nữ', 'Giày dép',
            'Gia dụng', 'Sách', 'Thể thao', 'Đồng hồ'
        ]

        products = []
        for i in range(1, 201):  # 200 sample products
            product_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f'product_{i}@ecommerce.local')
            category = categories[i % len(categories)]
            products.append({
                'id': str(product_uuid),
                'name': f'Product {i}',
                'category_name': category
            })

        return products

    def _choose_action(self, user_viewed, user_carted, user_wishlisted=None):
        """
        Choose action based on weights and user state
        Implements realistic funnel behavior with 8 actions
        """
        user_wishlisted = user_wishlisted or []

        # If user has items in cart, higher chance of purchase
        if user_carted and random.random() < 0.3:
            return 'purchase'

        # If user has viewed items, higher chance of cart
        if user_viewed and random.random() < 0.25:
            if random.random() < 0.7:
                return 'add_to_cart'
            else:
                return 'add_to_wishlist'

        # Small chance to remove from cart
        if user_carted and random.random() < 0.1:
            return 'remove_from_cart'

        # Otherwise use standard weights
        rand = random.random()
        cumulative = 0
        for action, weight in self.ACTION_WEIGHTS.items():
            cumulative += weight
            if rand < cumulative:
                return action

        return 'view_product'  # Default fallback

    def _pick_product(self, products, preferred_cats, products_by_category):
        """Pick a product, biased towards preferred categories"""
        if not products:
            return None

        # 70% chance to pick from preferred categories
        if preferred_cats and random.random() < 0.7:
            for cat in random.sample(preferred_cats, len(preferred_cats)):
                if products_by_category.get(cat):
                    product = random.choice(products_by_category[cat])
                    return product['id']

        # Random product
        product = random.choice(products)
        return product['id']

    def _print_statistics(self, total_behaviors):
        """Print behavior statistics"""
        from django.db.models import Count

        stats = UserBehavior.objects.values('action').annotate(
            count=Count('id')
        ).order_by('-count')

        self.stdout.write(self.style.SUCCESS(
            f'\n=== Behavior Seeding Complete ===\n'
            f'Total behaviors: {total_behaviors:,}'
        ))

        self.stdout.write('\nAction distribution:')
        for stat in stats:
            action = stat['action']
            count = stat['count']
            pct = (count / total_behaviors * 100) if total_behaviors > 0 else 0
            bar = '█' * int(pct / 2)
            self.stdout.write(f'  {action:10s}: {count:6,} ({pct:5.1f}%) {bar}')

        # User stats
        user_stats = UserBehavior.objects.values('user_id').annotate(
            count=Count('id')
        ).order_by('-count')

        user_counts = [s['count'] for s in user_stats]
        if user_counts:
            avg_per_user = sum(user_counts) / len(user_counts)
            min_per_user = min(user_counts)
            max_per_user = max(user_counts)
            self.stdout.write(
                f'\nPer-user stats:\n'
                f'  Total users: {len(user_counts)}\n'
                f'  Avg behaviors/user: {avg_per_user:.1f}\n'
                f'  Min: {min_per_user}, Max: {max_per_user}'
            )
