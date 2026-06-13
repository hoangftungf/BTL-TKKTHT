"""
Prometheus Metrics cho AI Search Service.

Usage:
    from search_app.metrics import metrics
    metrics.requests_total.labels(mode='hybrid').inc()
"""
import logging
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY

logger = logging.getLogger(__name__)


class SearchMetrics:
    """Central metrics registry cho ai-search."""

    def __init__(self):
        # Request counts
        self.requests_total = Counter(
            'search_requests_total',
            'Total search requests',
            ['mode', 'status'],
        )
        self.autocomplete_requests_total = Counter(
            'search_autocomplete_requests_total',
            'Autocomplete requests',
        )
        self.errors_total = Counter(
            'search_errors_total',
            'Total errors',
            ['error_type'],
        )

        # Latency
        self.latency_seconds = Histogram(
            'search_latency_seconds',
            'Search latency by mode',
            ['mode'],
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
        )

        # Results
        self.results_count = Histogram(
            'search_results_count',
            'Number of search results returned',
            ['mode'],
            buckets=(0, 1, 5, 10, 20, 50, 100, 200),
        )

        # Index
        self.index_size = Gauge(
            'search_index_size',
            'Number of products in search index',
        )
        self.index_last_updated = Gauge(
            'search_index_last_updated_timestamp_seconds',
            'Timestamp of last index update',
        )

        # Event processing
        self.events_processed_total = Counter(
            'search_events_processed_total',
            'Domain events processed',
            ['event_type', 'status'],
        )


# Singleton
metrics = SearchMetrics()
