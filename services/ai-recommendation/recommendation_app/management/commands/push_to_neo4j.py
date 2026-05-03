"""
Push User Behaviors to Neo4j Graph Database

Creates:
- User nodes
- Product nodes (with category relationships)
- Category nodes
- Behavior relationships for 8 actions:
  - VIEW_PRODUCT
  - CLICK_PRODUCT
  - ADD_TO_CART
  - REMOVE_FROM_CART
  - PURCHASE
  - ADD_TO_WISHLIST
  - SEARCH
  - VIEW_CATEGORY

Optimizations:
- Batch processing (100-500 records per batch)
- Progress logging every 1000 records
- Avoids duplicate MERGE explosion
"""

import os
import logging
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import connection

from recommendation_app.models import UserBehavior

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Push user behaviors to Neo4j graph database'

    BATCH_SIZE = 200  # Records per batch

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing graph before pushing'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=200,
            help='Records per batch (default: 200)'
        )

    def handle(self, *args, **options):
        clear_existing = options['clear']
        batch_size = options['batch_size']

        self.stdout.write('Connecting to Neo4j...')

        try:
            from services.neo4j_client import get_driver, get_session, create_indexes
        except ImportError:
            # Fallback to local import
            from recommendation_app.knowledge_graph import get_neo4j_driver
            get_driver = get_neo4j_driver

            def get_session():
                driver = get_driver()
                if driver:
                    return driver.session()
                return None

            def create_indexes():
                pass

        driver = get_driver()
        if driver is None:
            self.stdout.write(self.style.ERROR(
                'Cannot connect to Neo4j. Check NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD'
            ))
            return

        self.stdout.write(self.style.SUCCESS('Connected to Neo4j'))

        # Clear if requested
        if clear_existing:
            self._clear_graph(driver)

        # Create indexes
        self._create_indexes(driver)

        # Fetch products with categories
        products = self._get_products_with_categories()
        self.stdout.write(f'Loaded {len(products)} products')

        # Get all behaviors
        total_behaviors = UserBehavior.objects.count()
        self.stdout.write(f'Processing {total_behaviors:,} behaviors...')

        if total_behaviors == 0:
            self.stdout.write(self.style.WARNING(
                'No behaviors found. Run seed_behaviors first.'
            ))
            return

        # Process in batches
        processed = 0
        batch_num = 0

        # First, create all unique users and products
        self._create_users_batch(driver)
        self._create_products_batch(driver, products)

        # Then create relationships
        behaviors = UserBehavior.objects.all().order_by('created_at').iterator(chunk_size=batch_size)

        batch = []
        for behavior in behaviors:
            # Normalize action names for Neo4j relationship types
            action = behavior.action.upper().replace('_', '_')
            batch.append({
                'user_id': str(behavior.user_id),
                'product_id': str(behavior.product_id) if behavior.product_id else None,
                'category_id': str(behavior.category_id) if behavior.category_id else None,
                'action': action,
                'search_query': behavior.search_query,
            })

            if len(batch) >= batch_size:
                self._push_behaviors_batch(driver, batch, products)
                processed += len(batch)
                batch_num += 1

                if processed % 1000 == 0:
                    self.stdout.write(f'  Processed {processed:,}/{total_behaviors:,} behaviors...')

                batch = []

        # Push remaining
        if batch:
            self._push_behaviors_batch(driver, batch, products)
            processed += len(batch)

        # Print summary
        self._print_summary(driver)

    def _clear_graph(self, driver):
        """Clear existing graph data"""
        self.stdout.write('Clearing existing graph...')
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        self.stdout.write('  Graph cleared')

    def _create_indexes(self, driver):
        """Create Neo4j indexes"""
        self.stdout.write('Creating indexes...')
        indexes = [
            "CREATE INDEX user_id IF NOT EXISTS FOR (u:User) ON (u.id)",
            "CREATE INDEX product_id IF NOT EXISTS FOR (p:Product) ON (p.id)",
            "CREATE INDEX category_name IF NOT EXISTS FOR (c:Category) ON (c.name)",
        ]

        with driver.session() as session:
            for query in indexes:
                try:
                    session.run(query)
                except Exception:
                    pass  # Index may already exist

        self.stdout.write('  Indexes created')

    def _get_products_with_categories(self):
        """Fetch products with their categories from product service"""
        import httpx

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
                    params={'page_size': 2000},
                    timeout=30.0
                )
                if response.status_code == 200:
                    data = response.json()
                    products = {}
                    for p in data.get('results', []):
                        # Handle both nested category object and category_name string
                        category = None
                        if p.get('category_name'):
                            category = p.get('category_name')
                        elif isinstance(p.get('category'), dict):
                            category = p.get('category', {}).get('name')

                        products[p['id']] = {
                            'name': p.get('name', ''),
                            'category': category,
                            'brand': p.get('brand', ''),
                            'price': p.get('price', 0),
                        }
                    self.stdout.write(f'  Fetched {len(products)} products from {endpoint}')
                    return products
            except Exception as e:
                self.stdout.write(f'  Warning: {endpoint} failed: {e}')

        return {}

    def _create_users_batch(self, driver):
        """Create all user nodes in batch"""
        self.stdout.write('Creating user nodes...')

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, username FROM ai_users")
                users = cursor.fetchall()
        except Exception:
            users = []

        if not users:
            # Get unique users from behaviors
            user_ids = UserBehavior.objects.values_list('user_id', flat=True).distinct()
            users = [(str(uid), f'user_{i}') for i, uid in enumerate(user_ids, 1)]

        with driver.session() as session:
            # Batch create users
            session.run(
                """
                UNWIND $users AS user
                MERGE (u:User {id: user.id})
                SET u.name = user.name
                """,
                users=[{'id': str(u[0]), 'name': u[1]} for u in users]
            )

        self.stdout.write(f'  Created {len(users)} user nodes')

    def _create_products_batch(self, driver, products):
        """Create product nodes with category relationships"""
        self.stdout.write('Creating product nodes...')

        if not products:
            # Get unique products from behaviors
            product_ids = UserBehavior.objects.exclude(
                product_id__isnull=True
            ).values_list('product_id', flat=True).distinct()

            products = {
                str(pid): {'name': f'Product {pid}', 'category': None}
                for pid in product_ids
            }

        # Prepare product data
        product_list = [
            {
                'id': pid,
                'name': p.get('name', ''),
                'category': p.get('category'),
                'brand': p.get('brand', ''),
                'price': p.get('price', 0),
            }
            for pid, p in products.items()
        ]

        with driver.session() as session:
            # Create products
            session.run(
                """
                UNWIND $products AS p
                MERGE (prod:Product {id: p.id})
                SET prod.name = p.name, prod.brand = p.brand, prod.price = p.price
                """,
                products=product_list
            )

            # Create categories and relationships
            categories = set(p.get('category') for p in product_list if p.get('category'))
            if categories:
                session.run(
                    """
                    UNWIND $categories AS cat
                    MERGE (c:Category {name: cat})
                    """,
                    categories=list(categories)
                )

                # Product-Category relationships
                product_categories = [
                    {'product_id': p['id'], 'category': p['category']}
                    for p in product_list if p.get('category')
                ]
                session.run(
                    """
                    UNWIND $items AS item
                    MATCH (p:Product {id: item.product_id})
                    MATCH (c:Category {name: item.category})
                    MERGE (p)-[:BELONGS_TO]->(c)
                    """,
                    items=product_categories
                )

        self.stdout.write(f'  Created {len(product_list)} product nodes')

    def _push_behaviors_batch(self, driver, batch, products):
        """Push a batch of behaviors to Neo4j - handles all 8 actions"""
        # Separate by action type for optimized queries
        view_products = [b for b in batch if b['action'] == 'VIEW_PRODUCT' and b['product_id']]
        click_products = [b for b in batch if b['action'] == 'CLICK_PRODUCT' and b['product_id']]
        add_to_carts = [b for b in batch if b['action'] == 'ADD_TO_CART' and b['product_id']]
        remove_from_carts = [b for b in batch if b['action'] == 'REMOVE_FROM_CART' and b['product_id']]
        purchases = [b for b in batch if b['action'] == 'PURCHASE' and b['product_id']]
        wishlists = [b for b in batch if b['action'] == 'ADD_TO_WISHLIST' and b['product_id']]
        searches = [b for b in batch if b['action'] == 'SEARCH']
        view_categories = [b for b in batch if b['action'] == 'VIEW_CATEGORY' and b['category_id']]

        # Legacy support
        views_legacy = [b for b in batch if b['action'] == 'VIEW' and b['product_id']]
        carts_legacy = [b for b in batch if b['action'] == 'CART' and b['product_id']]

        with driver.session() as session:
            # VIEW_PRODUCT relationships
            if view_products or views_legacy:
                session.run(
                    """
                    UNWIND $items AS item
                    MATCH (u:User {id: item.user_id})
                    MATCH (p:Product {id: item.product_id})
                    MERGE (u)-[r:VIEW_PRODUCT]->(p)
                    SET r.count = COALESCE(r.count, 0) + 1
                    """,
                    items=view_products + views_legacy
                )

            # CLICK_PRODUCT relationships
            if click_products:
                session.run(
                    """
                    UNWIND $items AS item
                    MATCH (u:User {id: item.user_id})
                    MATCH (p:Product {id: item.product_id})
                    MERGE (u)-[r:CLICK_PRODUCT]->(p)
                    SET r.count = COALESCE(r.count, 0) + 1
                    """,
                    items=click_products
                )

            # ADD_TO_CART relationships
            if add_to_carts or carts_legacy:
                session.run(
                    """
                    UNWIND $items AS item
                    MATCH (u:User {id: item.user_id})
                    MATCH (p:Product {id: item.product_id})
                    MERGE (u)-[r:ADD_TO_CART]->(p)
                    SET r.count = COALESCE(r.count, 0) + 1
                    """,
                    items=add_to_carts + carts_legacy
                )

            # REMOVE_FROM_CART relationships
            if remove_from_carts:
                session.run(
                    """
                    UNWIND $items AS item
                    MATCH (u:User {id: item.user_id})
                    MATCH (p:Product {id: item.product_id})
                    MERGE (u)-[r:REMOVE_FROM_CART]->(p)
                    SET r.count = COALESCE(r.count, 0) + 1
                    """,
                    items=remove_from_carts
                )

            # PURCHASE relationships
            if purchases:
                session.run(
                    """
                    UNWIND $items AS item
                    MATCH (u:User {id: item.user_id})
                    MATCH (p:Product {id: item.product_id})
                    MERGE (u)-[r:PURCHASE]->(p)
                    SET r.count = COALESCE(r.count, 0) + 1
                    """,
                    items=purchases
                )

            # ADD_TO_WISHLIST relationships
            if wishlists:
                session.run(
                    """
                    UNWIND $items AS item
                    MATCH (u:User {id: item.user_id})
                    MATCH (p:Product {id: item.product_id})
                    MERGE (u)-[r:ADD_TO_WISHLIST]->(p)
                    SET r.count = COALESCE(r.count, 0) + 1
                    """,
                    items=wishlists
                )

            # SEARCH relationships (to product if exists)
            search_with_product = [s for s in searches if s['product_id']]
            if search_with_product:
                session.run(
                    """
                    UNWIND $items AS item
                    MATCH (u:User {id: item.user_id})
                    MATCH (p:Product {id: item.product_id})
                    MERGE (u)-[r:SEARCH]->(p)
                    SET r.query = item.search_query
                    """,
                    items=search_with_product
                )

            # VIEW_CATEGORY relationships
            if view_categories:
                # First ensure categories exist
                session.run(
                    """
                    UNWIND $items AS item
                    MERGE (c:Category {id: item.category_id})
                    """,
                    items=view_categories
                )
                session.run(
                    """
                    UNWIND $items AS item
                    MATCH (u:User {id: item.user_id})
                    MATCH (c:Category {id: item.category_id})
                    MERGE (u)-[r:VIEW_CATEGORY]->(c)
                    SET r.count = COALESCE(r.count, 0) + 1
                    """,
                    items=view_categories
                )

    def _print_summary(self, driver):
        """Print final summary statistics"""
        with driver.session() as session:
            # Count nodes
            users = session.run("MATCH (u:User) RETURN COUNT(u) AS c").single()['c']
            products = session.run("MATCH (p:Product) RETURN COUNT(p) AS c").single()['c']
            categories = session.run("MATCH (c:Category) RETURN COUNT(c) AS c").single()['c']

            # Count relationships for all 8 actions
            view_products = session.run("MATCH ()-[r:VIEW_PRODUCT]->() RETURN COUNT(r) AS c").single()['c']
            click_products = session.run("MATCH ()-[r:CLICK_PRODUCT]->() RETURN COUNT(r) AS c").single()['c']
            add_to_carts = session.run("MATCH ()-[r:ADD_TO_CART]->() RETURN COUNT(r) AS c").single()['c']
            remove_from_carts = session.run("MATCH ()-[r:REMOVE_FROM_CART]->() RETURN COUNT(r) AS c").single()['c']
            purchases = session.run("MATCH ()-[r:PURCHASE]->() RETURN COUNT(r) AS c").single()['c']
            wishlists = session.run("MATCH ()-[r:ADD_TO_WISHLIST]->() RETURN COUNT(r) AS c").single()['c']
            searches = session.run("MATCH ()-[r:SEARCH]->() RETURN COUNT(r) AS c").single()['c']
            view_categories = session.run("MATCH ()-[r:VIEW_CATEGORY]->() RETURN COUNT(r) AS c").single()['c']
            belongs = session.run("MATCH ()-[r:BELONGS_TO]->() RETURN COUNT(r) AS c").single()['c']

            total_actions = (view_products + click_products + add_to_carts + remove_from_carts +
                           purchases + wishlists + searches + view_categories)

        self.stdout.write(self.style.SUCCESS(
            f'\n=== Neo4j Push Complete ===\n'
            f'\nNodes:\n'
            f'  Users: {users:,}\n'
            f'  Products: {products:,}\n'
            f'  Categories: {categories:,}\n'
            f'\nBehavior Relationships (8 Actions):\n'
            f'  VIEW_PRODUCT: {view_products:,}\n'
            f'  CLICK_PRODUCT: {click_products:,}\n'
            f'  ADD_TO_CART: {add_to_carts:,}\n'
            f'  REMOVE_FROM_CART: {remove_from_carts:,}\n'
            f'  PURCHASE: {purchases:,}\n'
            f'  ADD_TO_WISHLIST: {wishlists:,}\n'
            f'  SEARCH: {searches:,}\n'
            f'  VIEW_CATEGORY: {view_categories:,}\n'
            f'\nOther Relationships:\n'
            f'  BELONGS_TO: {belongs:,}\n'
            f'\nTotal Action Relationships: {total_actions:,}'
        ))
