"""
Validate AI Pipeline Data
Checks:
- Users count (target: 500+)
- Behaviors count (target: 10,000+)
- Per-user behaviors (target: 20+ per user)
- All 8 actions present
- Neo4j nodes and relationships
- Data integrity
"""

import logging
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count

from recommendation_app.models import UserBehavior

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Validate AI pipeline data in PostgreSQL and Neo4j'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('AI PIPELINE VALIDATION')
        self.stdout.write('=' * 60)

        # PostgreSQL validation
        self._validate_postgres()

        # Neo4j validation
        self._validate_neo4j()

        self.stdout.write(self.style.SUCCESS('\n✓ Validation complete'))

    def _validate_postgres(self):
        """Validate PostgreSQL data"""
        self.stdout.write('\n--- PostgreSQL Data ---')

        # Users
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM ai_users")
                user_count = cursor.fetchone()[0]
                self.stdout.write(f'Users (ai_users): {user_count:,}')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Users table: {e}'))
            user_count = 0

        # Behaviors
        behavior_count = UserBehavior.objects.count()
        self.stdout.write(f'Behaviors: {behavior_count:,}')

        if behavior_count > 0:
            # Action distribution
            stats = UserBehavior.objects.values('action').annotate(
                count=Count('id')
            ).order_by('-count')

            self.stdout.write('\nAction Distribution:')
            for stat in stats:
                pct = stat['count'] / behavior_count * 100
                self.stdout.write(
                    f"  {stat['action']:10s}: {stat['count']:6,} ({pct:5.1f}%)"
                )

            # Users with behaviors
            users_with_behaviors = UserBehavior.objects.values(
                'user_id'
            ).distinct().count()
            self.stdout.write(f'\nUsers with behaviors: {users_with_behaviors:,}')

            # Products referenced
            products_referenced = UserBehavior.objects.exclude(
                product_id__isnull=True
            ).values('product_id').distinct().count()
            self.stdout.write(f'Products referenced: {products_referenced:,}')

            # Behaviors per user stats
            user_stats = UserBehavior.objects.values('user_id').annotate(
                count=Count('id')
            )
            counts = [s['count'] for s in user_stats]
            if counts:
                avg_per_user = sum(counts) / len(counts)
                min_per_user = min(counts)
                max_per_user = max(counts)
                self.stdout.write(
                    f'\nBehaviors per user: avg={avg_per_user:.1f}, '
                    f'min={min_per_user}, max={max_per_user}'
                )

                # Validation checks
                self.stdout.write('\n--- Validation Checks ---')

                # Check total behaviors >= 10,000
                if behavior_count >= 10000:
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Total behaviors >= 10,000: {behavior_count:,}'
                    ))
                else:
                    self.stdout.write(self.style.ERROR(
                        f'✗ Total behaviors < 10,000: {behavior_count:,}'
                    ))

                # Check each user >= 20 behaviors
                if min_per_user >= 20:
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ All users have >= 20 behaviors (min: {min_per_user})'
                    ))
                else:
                    users_below_20 = len([c for c in counts if c < 20])
                    self.stdout.write(self.style.ERROR(
                        f'✗ {users_below_20} users have < 20 behaviors (min: {min_per_user})'
                    ))

                # Check all 8 actions present
                required_actions = [
                    'view_product', 'click_product', 'add_to_cart', 'remove_from_cart',
                    'purchase', 'add_to_wishlist', 'search', 'view_category'
                ]
                present_actions = set(s['action'] for s in stats)
                missing_actions = set(required_actions) - present_actions
                if not missing_actions:
                    self.stdout.write(self.style.SUCCESS(
                        '✓ All 8 required actions present'
                    ))
                else:
                    self.stdout.write(self.style.ERROR(
                        f'✗ Missing actions: {", ".join(missing_actions)}'
                    ))

    def _validate_neo4j(self):
        """Validate Neo4j data"""
        self.stdout.write('\n--- Neo4j Graph ---')

        try:
            from services.neo4j_client import get_driver
        except ImportError:
            try:
                from recommendation_app.knowledge_graph import get_neo4j_driver as get_driver
            except ImportError:
                self.stdout.write(self.style.WARNING('Neo4j client not available'))
                return

        driver = get_driver()
        if driver is None:
            self.stdout.write(self.style.WARNING('Cannot connect to Neo4j'))
            return

        with driver.session() as session:
            # Node counts
            users = session.run("MATCH (u:User) RETURN COUNT(u) AS c").single()['c']
            products = session.run("MATCH (p:Product) RETURN COUNT(p) AS c").single()['c']
            categories = session.run("MATCH (c:Category) RETURN COUNT(c) AS c").single()['c']

            self.stdout.write(f'\nNodes:')
            self.stdout.write(f'  Users: {users:,}')
            self.stdout.write(f'  Products: {products:,}')
            self.stdout.write(f'  Categories: {categories:,}')
            self.stdout.write(f'  Total: {users + products + categories:,}')

            # Relationship counts - 8 core actions
            action_rel_types = [
                'VIEW_PRODUCT', 'CLICK_PRODUCT', 'ADD_TO_CART', 'REMOVE_FROM_CART',
                'PURCHASE', 'ADD_TO_WISHLIST', 'SEARCH', 'VIEW_CATEGORY'
            ]
            # Other relationship types
            other_rel_types = ['BELONGS_TO', 'SIMILAR_TO', 'INTEREST', 'BOUGHT_TOGETHER']

            self.stdout.write(f'\nBehavior Relationships (8 Actions):')
            total_action_rels = 0
            missing_actions = []
            for rel_type in action_rel_types:
                count = session.run(
                    f"MATCH ()-[r:{rel_type}]->() RETURN COUNT(r) AS c"
                ).single()['c']
                if count > 0:
                    self.stdout.write(f'  {rel_type}: {count:,}')
                    total_action_rels += count
                else:
                    missing_actions.append(rel_type)

            self.stdout.write(f'\nOther Relationships:')
            total_other_rels = 0
            for rel_type in other_rel_types:
                count = session.run(
                    f"MATCH ()-[r:{rel_type}]->() RETURN COUNT(r) AS c"
                ).single()['c']
                if count > 0:
                    self.stdout.write(f'  {rel_type}: {count:,}')
                    total_other_rels += count

            self.stdout.write(f'\nTotal action relationships: {total_action_rels:,}')

            # Missing actions warning
            if missing_actions:
                self.stdout.write(self.style.WARNING(
                    f'\n⚠ Missing actions in graph: {", ".join(missing_actions)}'
                ))

            # Graph density check
            if users > 0 and products > 0:
                view_count = session.run(
                    "MATCH ()-[r:VIEW_PRODUCT]->() RETURN COUNT(r) AS c"
                ).single()['c']
                density = view_count / (users * products) * 100
                self.stdout.write(f'\nGraph density (VIEW_PRODUCT): {density:.4f}%')

            # Sample data
            self.stdout.write('\nSample VIEW_PRODUCT relationships:')
            samples = session.run("""
                MATCH (u:User)-[r:VIEW_PRODUCT]->(p:Product)
                RETURN u.id AS user, p.name AS product, r.count AS views
                LIMIT 5
            """)
            for record in samples:
                user = record['user'][:20] if record['user'] else 'Unknown'
                product = record['product'][:30] if record['product'] else 'Unknown'
                views = record['views'] or 1
                self.stdout.write(f'  {user} -> {product} ({views} views)')
