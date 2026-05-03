"""
Seed 500 Users for AI Pipeline
Creates users with format: user_1 to user_500
"""

import uuid
import logging
from django.core.management.base import BaseCommand
from django.db import connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Seed 500 users for AI behavior pipeline'

    NUM_USERS = 500

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=500,
            help='Number of users to create (default: 500)'
        )

    def handle(self, *args, **options):
        num_users = options['count']
        self.stdout.write(f'Seeding {num_users} users...')

        # We store user UUIDs in a local table since this service
        # doesn't have access to auth_db directly
        # Create a local users reference table if not exists
        self._ensure_users_table()

        users_created = 0
        users_existing = 0

        # Generate deterministic UUIDs for reproducibility
        for i in range(1, num_users + 1):
            # Generate consistent UUID based on user number
            user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f'user_{i}@ecommerce.local')
            username = f'user_{i}'
            email = f'user_{i}@ecommerce.local'

            created = self._create_or_get_user(user_uuid, username, email)
            if created:
                users_created += 1
            else:
                users_existing += 1

            if i % 100 == 0:
                self.stdout.write(f'  Processed {i}/{num_users} users...')

        self.stdout.write(self.style.SUCCESS(
            f'\n=== User Seeding Complete ===\n'
            f'Total users: {num_users}\n'
            f'Created: {users_created}\n'
            f'Already existing: {users_existing}'
        ))

        # Print sample user IDs for testing
        self.stdout.write('\nSample User IDs for testing:')
        for i in [1, 10, 100, 250, 500]:
            if i <= num_users:
                user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f'user_{i}@ecommerce.local')
                self.stdout.write(f'  user_{i}: {user_uuid}')

    def _ensure_users_table(self):
        """Create local users reference table if not exists"""
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_users (
                    id UUID PRIMARY KEY,
                    username VARCHAR(150) UNIQUE NOT NULL,
                    email VARCHAR(254) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ai_users_username ON ai_users(username)
            """)

    def _create_or_get_user(self, user_id, username, email):
        """Create user if not exists, return True if created"""
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO ai_users (id, username, email)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                RETURNING id
                """,
                [str(user_id), username, email]
            )
            result = cursor.fetchone()
            return result is not None
