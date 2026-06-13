"""
Prometheus Metrics cho AI Recommendation Service.

Usage:
    from recommendation_app.metrics import metrics
    metrics.requests_total.labels(source='similar').inc()
"""
import logging
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY

logger = logging.getLogger(__name__)


class RecommendationMetrics:
    """Central metrics registry cho ai-recommendation."""

    def __init__(self):
        # Request counts by source
        self.requests_total = Counter(
            'recommendation_requests_total',
            'Total recommendation requests',
            ['source', 'status'],
        )
        self.errors_total = Counter(
            'recommendation_errors_total',
            'Total errors',
            ['error_type'],
        )

        # Latency
        self.latency_seconds = Histogram(
            'recommendation_latency_seconds',
            'Recommendation generation latency',
            ['source'],
            buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0),
        )

        # KG metrics
        self.kg_query_latency = Histogram(
            'recommendation_kg_query_latency_seconds',
            'Neo4j query latency',
            ['query_type'],
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0),
        )
        self.kg_products_total = Gauge(
            'recommendation_kg_products_total',
            'Number of products in KG',
        )
        self.kg_relationships_total = Gauge(
            'recommendation_kg_relationships_total',
            'Number of relationships in KG',
        )

        # Event processing
        self.events_processed_total = Counter(
            'recommendation_events_processed_total',
            'Domain events processed',
            ['event_type', 'status'],
        )

        # Hybrid engine distribution
        self.engine_source_distribution = Counter(
            'recommendation_engine_source_total',
            'Recommendations by engine source',
            ['source'],
        )


# Singleton
metrics = RecommendationMetrics()
