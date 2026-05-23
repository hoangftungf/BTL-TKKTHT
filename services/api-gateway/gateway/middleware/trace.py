"""
Distributed Tracing Middleware
Generates or propagates X-Trace-Id header for cross-service request tracking.
"""
import logging
import threading
import uuid

logger = logging.getLogger(__name__)

# Thread-local storage: any code running inside the request can call
# get_current_trace_id() without needing to pass trace_id through every function.
_trace_ctx = threading.local()


def get_current_trace_id() -> str:
    """Return the active trace ID for this request thread, or a fresh UUID."""
    return getattr(_trace_ctx, 'trace_id', None) or str(uuid.uuid4())


def make_traced_headers(extra: dict = None) -> dict:
    """
    Build an HTTP headers dict with the current X-Trace-Id.
    Use this for every outbound httpx / requests call so the trace propagates.

    Examples:
        httpx.get(url, headers=make_traced_headers())
        httpx.post(url, json=body, headers=make_traced_headers({'Authorization': token}))
    """
    headers = {'X-Trace-Id': get_current_trace_id()}
    if extra:
        headers.update(extra)
    return headers


class TraceMiddleware:
    """
    Django WSGI middleware for distributed request tracing.

    Behaviour:
    - Reads X-Trace-Id from the incoming request (propagation from upstream).
    - Generates a new UUID v4 when none is present (service entry point).
    - Stores trace_id in thread-local so downstream code can access it via
      get_current_trace_id() without threading the value through every call.
    - Echoes the trace_id in the response X-Trace-Id header.
    - Clears thread-local on completion to avoid cross-request leaks
      when threads are reused by gunicorn / uWSGI worker pools.

    Setup — add FIRST in settings.py MIDDLEWARE list:
        MIDDLEWARE = [
            'gateway.middleware.trace.TraceMiddleware',
            'gateway.middleware.rate_limit.RateLimitMiddleware',
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
            _trace_ctx.trace_id = None  # prevent thread-pool reuse contamination

        response[self.HEADER] = trace_id
        return response
