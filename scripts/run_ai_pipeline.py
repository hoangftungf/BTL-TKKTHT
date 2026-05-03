#!/usr/bin/env python
"""
Master script to run the complete AI behavior pipeline

Steps:
1. Seed 500 users
2. Seed 10,000-20,000 behaviors
3. Push data to Neo4j
4. Enhance graph with relationships
5. Validate pipeline

Usage:
    # Docker (recommended)
    docker-compose exec ai-recommendation python manage.py run_full_pipeline

    # Standalone
    python scripts/run_ai_pipeline.py

    # With options
    python scripts/run_ai_pipeline.py --users 500 --clear
"""

import os
import sys

# Add project path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
service_path = os.path.join(project_root, 'services', 'ai-recommendation')
sys.path.insert(0, service_path)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recommendation_project.settings')

import django
django.setup()

from django.core.management import call_command


def main():
    """Run the full pipeline"""
    print("=" * 60)
    print("AI USER BEHAVIOR PIPELINE")
    print("=" * 60)

    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run full AI pipeline')
    parser.add_argument('--users', type=int, default=500, help='Number of users')
    parser.add_argument('--min-behaviors', type=int, default=20)
    parser.add_argument('--max-behaviors', type=int, default=50)
    parser.add_argument('--clear', action='store_true', help='Clear existing data')
    parser.add_argument('--skip-neo4j', action='store_true', help='Skip Neo4j steps')
    args = parser.parse_args()

    # Run command
    call_command(
        'run_full_pipeline',
        users=args.users,
        min_behaviors=args.min_behaviors,
        max_behaviors=args.max_behaviors,
        clear=args.clear,
        skip_neo4j=args.skip_neo4j
    )


if __name__ == '__main__':
    main()
