#!/usr/bin/env python
"""
Standalone script to seed 500 users
Can be run from scripts/ directory or via Docker

Usage:
    # Local development
    cd services/ai-recommendation
    python manage.py seed_users --count 500

    # Docker
    docker-compose exec ai-recommendation python manage.py seed_users --count 500

    # Standalone (requires Django setup)
    python scripts/seed_users.py
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
    """Run the seed_users command"""
    print("=" * 60)
    print("SEED USERS SCRIPT")
    print("=" * 60)

    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description='Seed users for AI pipeline')
    parser.add_argument('--count', type=int, default=500, help='Number of users')
    args = parser.parse_args()

    # Run command
    call_command('seed_users', count=args.count)

    print("\nDone! Run seed_behaviors.py next.")


if __name__ == '__main__':
    main()
