"""
Run Full AI Pipeline
Executes all steps in sequence:
1. Seed 500 users
2. Seed 10,000-20,000 behaviors
3. Push to Neo4j
4. Enhance graph with relationships
5. Validate data
"""

import logging
from django.core.management.base import BaseCommand
from django.core.management import call_command

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run the complete AI behavior pipeline'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=500,
            help='Number of users to create (default: 500)'
        )
        parser.add_argument(
            '--min-behaviors',
            type=int,
            default=20,
            help='Minimum behaviors per user (default: 20)'
        )
        parser.add_argument(
            '--max-behaviors',
            type=int,
            default=50,
            help='Maximum behaviors per user (default: 50)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding'
        )
        parser.add_argument(
            '--skip-neo4j',
            action='store_true',
            help='Skip Neo4j push and enhancement'
        )

    def handle(self, *args, **options):
        num_users = options['users']
        min_behaviors = options['min_behaviors']
        max_behaviors = options['max_behaviors']
        clear = options['clear']
        skip_neo4j = options['skip_neo4j']

        self.stdout.write(self.style.SUCCESS(
            '\n' + '=' * 60 + '\n'
            'AI USER BEHAVIOR PIPELINE\n'
            '=' * 60
        ))

        # Step 1: Seed Users
        self.stdout.write(self.style.HTTP_INFO(
            '\n[STEP 1/5] Seeding Users...'
        ))
        call_command('seed_users', count=num_users)

        # Step 2: Seed Behaviors
        self.stdout.write(self.style.HTTP_INFO(
            '\n[STEP 2/5] Seeding Behaviors...'
        ))
        call_command(
            'seed_behaviors',
            min_interactions=min_behaviors,
            max_interactions=max_behaviors,
            clear=clear
        )

        if not skip_neo4j:
            # Step 3: Push to Neo4j
            self.stdout.write(self.style.HTTP_INFO(
                '\n[STEP 3/5] Pushing to Neo4j...'
            ))
            try:
                call_command('push_to_neo4j', clear=clear)
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f'Neo4j push failed: {e}\n'
                    'Continuing with remaining steps...'
                ))

            # Step 4: Enhance Graph
            self.stdout.write(self.style.HTTP_INFO(
                '\n[STEP 4/5] Enhancing Graph...'
            ))
            try:
                call_command('enhance_graph')
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f'Graph enhancement failed: {e}'
                ))
        else:
            self.stdout.write(self.style.WARNING(
                '\n[STEP 3/5] Skipping Neo4j push...'
                '\n[STEP 4/5] Skipping graph enhancement...'
            ))

        # Step 5: Validate
        self.stdout.write(self.style.HTTP_INFO(
            '\n[STEP 5/5] Validating Pipeline...'
        ))
        call_command('validate_pipeline')

        self.stdout.write(self.style.SUCCESS(
            '\n' + '=' * 60 + '\n'
            'PIPELINE COMPLETE!\n'
            '=' * 60 + '\n'
            f'\nResults:\n'
            f'  - {num_users} users created\n'
            f'  - {min_behaviors}-{max_behaviors} behaviors per user\n'
            f'  - ~{num_users * (min_behaviors + max_behaviors) // 2:,} total behaviors\n'
            f'\nNext steps:\n'
            f'  1. Use data for AI model training\n'
            f'  2. Query Neo4j for recommendations\n'
            f'  3. Integrate with RAG chatbot\n'
        ))
