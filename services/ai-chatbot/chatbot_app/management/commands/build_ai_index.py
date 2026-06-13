"""
Management command: build_ai_index
====================================
Pre-builds the FAISS vector index for the AI chatbot so the service starts up
fast without blocking any request thread on the first chat message.

Uses unified AI Core components (Phase 2.1).

Usage:
    python manage.py build_ai_index
    python manage.py build_ai_index --index-dir /data/ai_index
    python manage.py build_ai_index --page-size 1000

Typical deployment workflow:
    1. Build Docker image
    2. In the init container / startup script, run this command ONCE.
    3. Mount AI_INDEX_DIR as a shared Docker volume between the init container
       and the chatbot service container so the index is ready at startup.
    4. Start the chatbot service — RAGPipeline.__init__ loads the index from
       disk in < 1 s instead of rebuilding it (which takes minutes).
"""

import os
import time

import httpx
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from lib.ai_core.embedder import embedder
from lib.ai_core.vector_store import vector_store


class Command(BaseCommand):
    help = 'Build and save the FAISS product embedding index for the AI chatbot.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--index-dir',
            default=None,
            help='Directory to save the index (default: settings.AI_INDEX_DIR or /app/ai_index)',
        )
        parser.add_argument(
            '--page-size',
            type=int,
            default=500,
            help='Number of products to fetch per request (default: 500)',
        )

    def handle(self, *args, **options):
        index_dir = options['index_dir'] or getattr(settings, 'AI_INDEX_DIR', '/app/ai_index')
        page_size = options['page_size']
        product_url = getattr(
            settings, 'PRODUCT_SERVICE_URL', 'http://product-service:8000/api/products'
        )

        self.stdout.write(f'[build_ai_index] Fetching products from {product_url} ...')

        # ── 1. Fetch products ────────────────────────────────────────────────
        try:
            resp = httpx.get(f'{product_url}?page_size={page_size}', timeout=30.0)
            resp.raise_for_status()
            products = resp.json().get('results', [])
        except Exception as exc:
            raise CommandError(f'Failed to fetch products: {exc}') from exc

        if not products:
            raise CommandError('Product service returned 0 products — nothing to index.')

        self.stdout.write(f'[build_ai_index] Fetched {len(products)} products.')

        # ── 2. Bulk index (handles ACL normalization + embedding + FAISS add) ─
        self.stdout.write('[build_ai_index] Generating embeddings and indexing ...')

        t0 = time.perf_counter()
        count = vector_store.bulk_index(products, embedder)
        elapsed = time.perf_counter() - t0

        if count == 0:
            raise CommandError('Indexing returned 0 products — something went wrong.')

        self.stdout.write(
            f'[build_ai_index] Indexed {count} products, elapsed {elapsed:.1f}s'
        )

        # ── 3. Persist to disk ───────────────────────────────────────────────
        ok = vector_store.save(index_dir)
        if not ok:
            raise CommandError(f'Failed to save index to {index_dir}')

        self.stdout.write(
            self.style.SUCCESS(
                f'[build_ai_index] DONE — index saved to {index_dir} '
                f'({count} products, {elapsed:.1f}s total time)'
            )
        )
