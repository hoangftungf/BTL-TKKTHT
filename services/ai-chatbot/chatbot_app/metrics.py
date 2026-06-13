"""
Prometheus Metrics cho AI Chatbot Service.

Khởi tạo metrics registry và expose endpoint để Prometheus scrape.
Sử dụng prometheus-client thay vì django-prometheus để tránh middleware conflicts.

Usage:
    from chatbot_app.metrics import metrics

    @metrics.track_latency('chat')
    def my_handler():
        ...
"""
import logging
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY

logger = logging.getLogger(__name__)


class ChatbotMetrics:
    """Central metrics registry cho ai-chatbot."""

    def __init__(self):
        # Request counts
        self.requests_total = Counter(
            'chatbot_requests_total',
            'Total chat requests',
            ['intent', 'status'],
        )
        self.errors_total = Counter(
            'chatbot_errors_total',
            'Total errors',
            ['error_type'],
        )

        # Latency
        self.latency_seconds = Histogram(
            'chatbot_latency_seconds',
            'Chat response latency in seconds',
            ['intent'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
        )

        # Cache
        self.cache_hits_total = Counter(
            'chatbot_cache_hits_total',
            'Semantic cache hits',
            ['cache_type'],
        )
        self.cache_misses_total = Counter(
            'chatbot_cache_misses_total',
            'Semantic cache misses',
            ['cache_type'],
        )

        # Context tracking
        self.context_length = Gauge(
            'chatbot_context_length',
            'Number of products in context',
        )
        self.ollama_latency_seconds = Histogram(
            'chatbot_ollama_latency_seconds',
            'Ollama LLM request latency',
            ['model'],
            buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0),
        )

        # Event processing
        self.events_processed_total = Counter(
            'chatbot_events_processed_total',
            'Domain events processed',
            ['event_type', 'status'],
        )

    def track_latency(self, intent='chat'):
        """Context manager to track operation latency."""
        class _Tracker:
            def __init__(self, metric, intent):
                self.metric = metric
                self.intent = intent

            def __enter__(self):
                self.t0 = time.perf_counter()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                elapsed = time.perf_counter() - self.t0
                self.metric.labels(intent=self.intent).observe(elapsed)

        return _Tracker(self.latency_seconds, intent)


# Singleton
metrics = ChatbotMetrics()
