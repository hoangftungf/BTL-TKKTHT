import time
from django.conf import settings
from django.http import JsonResponse
from django.core.cache import cache


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit = getattr(settings, 'RATE_LIMIT_REQUESTS', 100)
        self.window = getattr(settings, 'RATE_LIMIT_WINDOW', 60)

    def __call__(self, request):
        if request.path.startswith('/admin/') or request.path == '/health/':
            return self.get_response(request)

        client_ip = self.get_client_ip(request)
        cache_key = f'rate_limit:{client_ip}'

        request_data = cache.get(cache_key, {'count': 0, 'start_time': time.time()})

        current_time = time.time()
        if current_time - request_data['start_time'] > self.window:
            request_data = {'count': 1, 'start_time': current_time}
        else:
            request_data['count'] += 1

        cache.set(cache_key, request_data, self.window)

        if request_data['count'] > self.rate_limit:
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'retry_after': int(self.window - (current_time - request_data['start_time']))
            }, status=429)

        response = self.get_response(request)
        response['X-RateLimit-Limit'] = str(self.rate_limit)
        response['X-RateLimit-Remaining'] = str(max(0, self.rate_limit - request_data['count']))
        response['X-RateLimit-Reset'] = str(int(request_data['start_time'] + self.window))

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
