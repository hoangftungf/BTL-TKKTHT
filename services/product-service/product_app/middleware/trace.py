"""
Distributed Tracing Middleware — product-service
=================================================
Reads or generates X-Trace-Id on every inbound request, stores it in
thread-local storage so any code on the same request thread can access
it via get_current_trace_id(), and echoes it in the response header.

Setup — add FIRST in product_project/settings.py MIDDLEWARE list:
    MIDDLEWARE = [
        'product_app.middleware.trace.TraceMiddleware',
        'corsheaders.middleware.CorsMiddleware',
        ...
    ]
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
    Build an HTTP headers dict containing the current X-Trace-Id.
    Pass this to every outbound httpx call so the trace propagates downstream.

    Examples:
        httpx.get(url, headers=make_traced_headers())
        httpx.post(url, json=body, headers=make_traced_headers({'Authorization': token}))
    """
    headers = {'X-Trace-Id': get_current_trace_id()}
    if extra:
        headers.update(extra)
    return headers


class TraceIdFilter(logging.Filter):
    """
    Logging filter that injects trace_id into every LogRecord so the
    formatter can render [Trace-ID: xxx] on every log line automatically.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_current_trace_id()
        return True


class TraceMiddleware:
    """
    Django WSGI middleware for distributed request tracing.

    Behaviour:
    - Reads X-Trace-Id from the incoming request (propagation from upstream).
    - Generates a new UUID v4 when none is present (service entry point).
    - Stores trace_id in thread-local so downstream code can call
      get_current_trace_id() without passing the value through every function.
    - Echoes trace_id in the response X-Trace-Id header.
    - Clears thread-local in the finally block to prevent cross-request
      contamination when gunicorn/uWSGI reuses worker threads.
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
            _trace_ctx.trace_id = None  # prevent thread-pool reuse contamination

        response[self.HEADER] = trace_id
        return response
