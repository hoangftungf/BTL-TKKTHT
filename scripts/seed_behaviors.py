#!/usr/bin/env python
"""
Standalone script to seed user behaviors
Creates 10,000-20,000 realistic user behavior records

Usage:
    # Local development
    cd services/ai-recommendation
    python manage.py seed_behaviors

    # Docker
    docker-compose exec ai-recommendation python manage.py seed_behaviors

    # Standalone (requires Django setup)
    python scripts/seed_behaviors.py
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
    """Run the seed_behaviors command"""
    print("=" * 60)
    print("SEED BEHAVIORS SCRIPT")
    print("=" * 60)

    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description='Seed behaviors for AI pipeline')
    parser.add_argument('--min', type=int, default=20, help='Min behaviors per user')
    parser.add_argument('--max', type=int, default=50, help='Max behaviors per user')
    parser.add_argument('--clear', action='store_true', help='Clear existing data')
    args = parser.parse_args()

    # Run command
    call_command(
        'seed_behaviors',
        min_interactions=args.min,
        max_interactions=args.max,
        clear=args.clear
    )

    print("\nDone! Run push_to_neo4j.py next.")


if __name__ == '__main__':
    main()
