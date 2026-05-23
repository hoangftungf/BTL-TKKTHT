"""
Management command: build_ai_index
====================================
Pre-builds the FAISS vector index for the AI chatbot so the service starts up
fast without blocking any request thread on the first chat message.

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

from chatbot_app.engine import ProductVectorStore, TextEmbedder


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

        # ── 2. Build text representations (with chunking) ───────────────────
        from chatbot_app.engine import RAGPipeline  # import here to avoid circular at module level

        texts = [RAGPipeline._build_product_text(p) for p in products]
        self.stdout.write(f'[build_ai_index] Built {len(texts)} text representations.')

        # ── 3. Generate embeddings ───────────────────────────────────────────
        ollama_host = getattr(settings, 'OLLAMA_HOST', 'http://ollama:11434')
        ollama_model = getattr(settings, 'OLLAMA_MODEL', 'llama3.2')

        embedder = TextEmbedder(ollama_host)
        self.stdout.write('[build_ai_index] Generating embeddings (this may take several minutes) ...')

        t0 = time.perf_counter()
        embeddings = embedder.embed(texts)
        elapsed = time.perf_counter() - t0

        if len(embeddings) == 0:
            raise CommandError('Embedding generation returned empty array.')

        self.stdout.write(
            f'[build_ai_index] Embeddings done — shape {embeddings.shape}, '
            f'elapsed {elapsed:.1f}s'
        )

        # ── 4. Populate vector store ─────────────────────────────────────────
        store = ProductVectorStore()
        for p, emb in zip(products, embeddings):
            cat = p.get('category', '')
            if isinstance(cat, dict):
                cat = cat.get('name', '')
            store.add(
                product_id=p['id'],
                embedding=emb,
                product_data={
                    'name': p.get('name', ''),
                    'price': p.get('price'),
                    'category': cat,
                    'brand': p.get('brand', ''),
                    'description': (p.get('description') or '')[:300],
                    'image_url': p.get('image_url', ''),
                },
            )

        self.stdout.write(f'[build_ai_index] Indexed {len(store.product_ids)} products.')

        # ── 5. Persist to disk ───────────────────────────────────────────────
        ok = store.save_local(index_dir)
        if not ok:
            raise CommandError(f'Failed to save index to {index_dir}')

        self.stdout.write(
            self.style.SUCCESS(
                f'[build_ai_index] DONE — index saved to {index_dir} '
                f'({len(store.product_ids)} products, {elapsed:.1f}s embedding time)'
            )
        )
