import json
import httpx
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        services_status = {}
        for name, url in settings.SERVICE_URLS.items():
            try:
                response = httpx.get(f"{url}/health/", timeout=5.0)
                services_status[name] = response.status_code == 200
            except Exception:
                services_status[name] = False

        all_healthy = all(services_status.values()) if services_status else True
        return Response({
            'status': 'healthy' if all_healthy else 'degraded',
            'services': services_status
        }, status=status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE)


class BaseProxyView(APIView):
    service_name = None
    permission_classes = [AllowAny]

    def get_service_url(self):
        return settings.SERVICE_URLS.get(self.service_name, '')

    def proxy_request(self, request, path=''):
        service_url = self.get_service_url()
        if not service_url:
            return Response(
                {'error': f'Service {self.service_name} not configured'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        url = f"{service_url}/{path}" if path else f"{service_url}/"
        if request.query_params:
            url += f"?{request.query_params.urlencode()}"

        headers = {
            key: value for key, value in request.headers.items()
            if key.lower() not in ['host', 'content-length']
        }

        # Prepare request body
        body = None
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            if request.data:
                body = json.dumps(request.data)
                headers['Content-Type'] = 'application/json'

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    method=request.method,
                    url=url,
                    headers=headers,
                    content=body,
                )
                return Response(
                    response.json() if response.content else None,
                    status=response.status_code
                )
        except httpx.ConnectError:
            return Response(
                {'error': f'Service {self.service_name} unavailable'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except httpx.TimeoutException:
            return Response(
                {'error': f'Service {self.service_name} timeout'},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get(self, request, path=''):
        return self.proxy_request(request, path)

    def post(self, request, path=''):
        return self.proxy_request(request, path)

    def put(self, request, path=''):
        return self.proxy_request(request, path)

    def patch(self, request, path=''):
        return self.proxy_request(request, path)

    def delete(self, request, path=''):
        return self.proxy_request(request, path)


class ProxyAuthView(BaseProxyView):
    service_name = 'auth'


class ProxyUserView(BaseProxyView):
    service_name = 'user'


class ProxyProductView(BaseProxyView):
    service_name = 'product'


class ProxyCartView(BaseProxyView):
    service_name = 'cart'


class ProxyOrderView(BaseProxyView):
    service_name = 'order'


class ProxyPaymentView(BaseProxyView):
    service_name = 'payment'


class ProxyShippingView(BaseProxyView):
    service_name = 'shipping'


class ProxyReviewView(BaseProxyView):
    service_name = 'review'


class ProxyNotificationView(BaseProxyView):
    service_name = 'notification'


class ProxyRecommendationView(BaseProxyView):
    service_name = 'ai_recommendation'


class ProxySearchView(BaseProxyView):
    service_name = 'ai_search'


class ProxyChatbotView(BaseProxyView):
    service_name = 'ai_chatbot'

    def get_service_url(self):
        return settings.SERVICE_URLS.get(self.service_name, '') + '/api/chatbot'


class ProxyAnalyticsView(BaseProxyView):
    service_name = 'ai_analytics'

    def get_service_url(self):
        return settings.SERVICE_URLS.get(self.service_name, '') + '/api/analytics'
