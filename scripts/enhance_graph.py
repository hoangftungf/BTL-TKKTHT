#!/usr/bin/env python
"""
Standalone script to enhance Neo4j graph
Creates intelligent relationships: SIMILAR_TO, INTEREST, popularity

Usage:
    # Local development
    cd services/ai-recommendation
    python manage.py enhance_graph

    # Docker
    docker-compose exec ai-recommendation python manage.py enhance_graph

    # Standalone (requires Django setup)
    python scripts/enhance_graph.py
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
    """Run the enhance_graph command"""
    print("=" * 60)
    print("ENHANCE GRAPH SCRIPT")
    print("=" * 60)

    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description='Enhance Neo4j graph')
    parser.add_argument('--min-co-views', type=int, default=2,
                       help='Min co-views for SIMILAR_TO')
    args = parser.parse_args()

    # Run command
    call_command('enhance_graph', min_co_views=args.min_co_views)

    print("\nDone! Graph is ready for recommendations.")


if __name__ == '__main__':
    main()
