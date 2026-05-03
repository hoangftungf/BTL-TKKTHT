#!/usr/bin/env python
"""
Standalone script to push data to Neo4j
Pushes users, products, and behaviors to graph database

Usage:
    # Local development
    cd services/ai-recommendation
    python manage.py push_to_neo4j

    # Docker
    docker-compose exec ai-recommendation python manage.py push_to_neo4j

    # Standalone (requires Django setup)
    python scripts/push_to_neo4j.py
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
    """Run the push_to_neo4j command"""
    print("=" * 60)
    print("PUSH TO NEO4J SCRIPT")
    print("=" * 60)

    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description='Push data to Neo4j')
    parser.add_argument('--clear', action='store_true', help='Clear existing graph')
    parser.add_argument('--batch-size', type=int, default=200, help='Batch size')
    args = parser.parse_args()

    # Run command
    call_command('push_to_neo4j', clear=args.clear, batch_size=args.batch_size)

    print("\nDone! Run enhance_graph.py next.")


if __name__ == '__main__':
    main()
