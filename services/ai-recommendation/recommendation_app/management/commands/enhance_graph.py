"""
Enhance Neo4j Graph with Intelligent Relationships

Creates:
1. SIMILAR_TO - Products viewed together by users
2. INTEREST - User interest in categories
3. Product popularity scores
4. Frequently bought together
5. User similarity based on behavior
"""

import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Enhance Neo4j graph with intelligent relationships'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-co-views',
            type=int,
            default=2,
            help='Minimum co-views for SIMILAR_TO relationship (default: 2)'
        )

    def handle(self, *args, **options):
        min_co_views = options['min_co_views']

        self.stdout.write('Connecting to Neo4j...')

        try:
            from services.neo4j_client import get_driver
        except ImportError:
            from recommendation_app.knowledge_graph import get_neo4j_driver as get_driver

        driver = get_driver()
        if driver is None:
            self.stdout.write(self.style.ERROR('Cannot connect to Neo4j'))
            return

        self.stdout.write(self.style.SUCCESS('Connected to Neo4j'))

        # Run enhancement queries
        self._create_similar_products(driver, min_co_views)
        self._create_user_interests(driver)
        self._set_product_popularity(driver)
        self._create_bought_together(driver)

        # Print summary
        self._print_summary(driver)

    def _create_similar_products(self, driver, min_co_views):
        """
        Create SIMILAR_TO relationships between products
        Based on: Users who viewed product A also viewed product B
        """
        self.stdout.write('Creating SIMILAR_TO relationships...')

        query = """
        // Find products viewed together by same users
        MATCH (u:User)-[:VIEW]->(p1:Product),
              (u)-[:VIEW]->(p2:Product)
        WHERE p1 <> p2 AND id(p1) < id(p2)
        WITH p1, p2, COUNT(DISTINCT u) AS co_views
        WHERE co_views >= $min_co_views
        MERGE (p1)-[r:SIMILAR_TO]->(p2)
        SET r.co_views = co_views,
            r.score = toFloat(co_views) / 10.0
        WITH p1, p2, r
        MERGE (p2)-[r2:SIMILAR_TO]->(p1)
        SET r2.co_views = r.co_views, r2.score = r.score
        RETURN COUNT(r) AS created
        """

        with driver.session() as session:
            result = session.run(query, min_co_views=min_co_views)
            count = result.single()['created']
            self.stdout.write(f'  Created {count:,} SIMILAR_TO relationships')

    def _create_user_interests(self, driver):
        """
        Create INTEREST relationships between users and categories
        Based on: Categories of products user has viewed/purchased
        """
        self.stdout.write('Creating user INTEREST relationships...')

        query = """
        // User interests based on views and purchases
        MATCH (u:User)-[r:VIEW|PURCHASE]->(p:Product)-[:BELONGS_TO]->(c:Category)
        WITH u, c,
             SUM(CASE WHEN TYPE(r) = 'PURCHASE' THEN 5 ELSE 1 END) AS interest_score
        WHERE interest_score >= 2
        MERGE (u)-[i:INTEREST]->(c)
        SET i.score = interest_score
        RETURN COUNT(i) AS created
        """

        with driver.session() as session:
            result = session.run(query)
            count = result.single()['created']
            self.stdout.write(f'  Created {count:,} INTEREST relationships')

    def _set_product_popularity(self, driver):
        """
        Set popularity score on products
        Based on: View count, cart count, purchase count
        """
        self.stdout.write('Setting product popularity scores...')

        query = """
        MATCH (p:Product)
        OPTIONAL MATCH (p)<-[v:VIEW]-()
        OPTIONAL MATCH (p)<-[c:CART]-()
        OPTIONAL MATCH (p)<-[pur:PURCHASE]-()
        WITH p,
             COALESCE(SUM(v.count), 0) AS views,
             COALESCE(SUM(c.count), 0) AS carts,
             COALESCE(SUM(pur.count), 0) AS purchases
        SET p.view_count = views,
            p.cart_count = carts,
            p.purchase_count = purchases,
            p.popularity = views + (carts * 3) + (purchases * 10)
        RETURN COUNT(p) AS updated
        """

        with driver.session() as session:
            result = session.run(query)
            count = result.single()['updated']
            self.stdout.write(f'  Updated popularity for {count:,} products')

    def _create_bought_together(self, driver):
        """
        Create BOUGHT_TOGETHER relationships
        Based on: Products purchased by the same user
        """
        self.stdout.write('Creating BOUGHT_TOGETHER relationships...')

        query = """
        // Find products purchased together
        MATCH (u:User)-[:PURCHASE]->(p1:Product),
              (u)-[:PURCHASE]->(p2:Product)
        WHERE p1 <> p2 AND id(p1) < id(p2)
        WITH p1, p2, COUNT(DISTINCT u) AS co_purchases
        WHERE co_purchases >= 1
        MERGE (p1)-[r:BOUGHT_TOGETHER]->(p2)
        SET r.count = co_purchases
        RETURN COUNT(r) AS created
        """

        with driver.session() as session:
            result = session.run(query)
            count = result.single()['created']
            self.stdout.write(f'  Created {count:,} BOUGHT_TOGETHER relationships')

    def _print_summary(self, driver):
        """Print enhancement summary"""
        with driver.session() as session:
            # Count enhanced relationships
            similar = session.run(
                "MATCH ()-[r:SIMILAR_TO]->() RETURN COUNT(r) AS c"
            ).single()['c']
            interest = session.run(
                "MATCH ()-[r:INTEREST]->() RETURN COUNT(r) AS c"
            ).single()['c']
            bought = session.run(
                "MATCH ()-[r:BOUGHT_TOGETHER]->() RETURN COUNT(r) AS c"
            ).single()['c']

            # Top popular products
            top_products_result = session.run("""
                MATCH (p:Product)
                WHERE p.popularity > 0
                RETURN p.name AS name, p.popularity AS popularity
                ORDER BY p.popularity DESC
                LIMIT 10
            """)
            top_products = list(top_products_result)

        self.stdout.write(self.style.SUCCESS(
            f'\n=== Graph Enhancement Complete ===\n'
            f'\nEnhanced Relationships:\n'
            f'  SIMILAR_TO: {similar:,}\n'
            f'  INTEREST: {interest:,}\n'
            f'  BOUGHT_TOGETHER: {bought:,}\n'
        ))

        self.stdout.write('\nTop 10 Popular Products:')
        for i, record in enumerate(top_products, 1):
            name = record['name'][:40] if record['name'] else 'Unknown'
            pop = record['popularity']
            self.stdout.write(f'  {i:2}. {name}: {pop}')

        # Print test queries
        self.stdout.write(self.style.SUCCESS(
            '\n=== Test Queries ===\n'
            '1. View user-product relationships:\n'
            '   MATCH (u:User)-[:VIEW]->(p:Product) RETURN u, p LIMIT 20\n'
            '\n2. View similar products:\n'
            '   MATCH (p1:Product)-[:SIMILAR_TO]->(p2:Product) RETURN p1, p2 LIMIT 20\n'
            '\n3. View user interests:\n'
            '   MATCH (u:User)-[:INTEREST]->(c:Category) RETURN u, c LIMIT 20\n'
            '\n4. View bought together:\n'
            '   MATCH (p1:Product)-[:BOUGHT_TOGETHER]->(p2:Product) RETURN p1, p2 LIMIT 20\n'
            '\n5. Get popular products:\n'
            '   MATCH (p:Product) WHERE p.popularity > 0 RETURN p ORDER BY p.popularity DESC LIMIT 20'
        ))
