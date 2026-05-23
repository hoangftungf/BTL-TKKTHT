"""
Distributed Tracing Middleware — ai-chatbot service
Same contract as gateway/middleware/trace.py; each service carries its own copy
because services run in separate Docker containers with no shared filesystem.
"""
import logging
import threading
import uuid

logger = logging.getLogger(__name__)

_trace_ctx = threading.local()


def get_current_trace_id() -> str:
    """Return the active trace ID for this request thread, or a fresh UUID."""
    return getattr(_trace_ctx, 'trace_id', None) or str(uuid.uuid4())


def make_traced_headers(extra: dict = None) -> dict:
    """
    Build headers dict with X-Trace-Id for outbound httpx calls.

    Usage:
        resp = httpx.get(ollama_url, headers=make_traced_headers())
        resp = httpx.post(product_url, json=body,
                          headers=make_traced_headers({'X-User-Id': uid}))
    """
    headers = {'X-Trace-Id': get_current_trace_id()}
    if extra:
        headers.update(extra)
    return headers


class TraceMiddleware:
    """
    Django WSGI middleware for distributed request tracing.

    Reads X-Trace-Id from the incoming request or generates a new UUID.
    Stores it in thread-local storage so engine.py can attach it to every
    outbound Ollama / product-service call via make_traced_headers().

    Setup (settings.py):
        MIDDLEWARE = [
            'chatbot_app.middleware.trace.TraceMiddleware',
            ...
        ]
    """

    HEADER = 'X-Trace-Id'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        trace_id = (
            request.headers.get(self.HEADER)
            or request.META.get('HTTP_X_TRACE_ID')
            or str(uuid.uuid4())
        )

        request.trace_id = trace_id
        _trace_ctx.trace_id = trace_id
        logger.debug('[TRACE] %s %s trace_id=%s', request.method, request.path, trace_id)

        try:
            response = self.get_response(request)
        finally:
            _trace_ctx.trace_id = None

        response[self.HEADER] = trace_id
        return response
