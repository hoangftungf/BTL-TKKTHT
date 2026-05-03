import logging
import httpx
import os
from threading import Thread
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer

logger = logging.getLogger(__name__)


def track_behavior(user_id, action, product_id=None, metadata=None):
    """Send tracking request to recommendation service (async)."""
    if not user_id:
        return

    def _send():
        try:
            url = os.environ.get('RECOMMENDATION_SERVICE_URL', 'http://ai-recommendation:8008')
            payload = {
                'user_id': str(user_id),
                'action': action,
                'product_id': str(product_id) if product_id else None,
                'metadata': metadata or {},
            }
            httpx.post(f"{url}/track/", json=payload, timeout=5.0)
        except Exception as e:
            logger.warning(f"Tracking error: {e}")

    thread = Thread(target=_send)
    thread.daemon = True
    thread.start()


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'healthy', 'service': 'cart-service'})


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.prefetch_related('items').get_or_create(user_id=request.user.id)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class CartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def get_product_info(self, product_id):
        try:
            response = httpx.get(f"{settings.PRODUCT_SERVICE_URL}/{product_id}/", timeout=5.0)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None

    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user_id=request.user.id)
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        variant_id = request.data.get('variant_id')

        product = self.get_product_info(product_id)
        if not product:
            return Response({'error': 'Sản phẩm không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

        if product.get('stock_quantity', 0) < quantity:
            return Response({'error': 'Sản phẩm không đủ số lượng'}, status=status.HTTP_400_BAD_REQUEST)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_id=product_id,
            variant_id=variant_id,
            defaults={
                'product_name': product.get('name', ''),
                'product_image': product.get('primary_image', {}).get('image', '') if product.get('primary_image') else '',
                'price': product.get('price', 0),
                'quantity': quantity,
            }
        )

        if not created:
            item.quantity += quantity
            item.save()

        # Track add_to_cart behavior
        track_behavior(
            user_id=request.user.id,
            action='add_to_cart',
            product_id=product_id,
            metadata={
                'quantity': quantity,
                'product_name': product.get('name', ''),
                'price': product.get('price', 0),
            }
        )

        return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def put(self, request, pk):
        cart, _ = Cart.objects.get_or_create(user_id=request.user.id)
        try:
            item = CartItem.objects.get(pk=pk, cart=cart)
        except CartItem.DoesNotExist:
            return Response({'error': 'Không tìm thấy sản phẩm trong giỏ hàng'}, status=status.HTTP_404_NOT_FOUND)

        quantity = int(request.data.get('quantity', item.quantity))
        if quantity <= 0:
            product_id = item.product_id
            product_name = item.product_name
            item.delete()

            # Track remove_from_cart behavior
            track_behavior(
                user_id=request.user.id,
                action='remove_from_cart',
                product_id=product_id,
                metadata={'product_name': product_name}
            )

            return Response({'message': 'Đã xóa sản phẩm khỏi giỏ hàng'})

        item.quantity = quantity
        item.save()
        return Response(CartItemSerializer(item).data)

    def delete(self, request, pk):
        cart, _ = Cart.objects.get_or_create(user_id=request.user.id)
        try:
            item = CartItem.objects.get(pk=pk, cart=cart)
            product_id = item.product_id
            product_name = item.product_name

            item.delete()

            # Track remove_from_cart behavior
            track_behavior(
                user_id=request.user.id,
                action='remove_from_cart',
                product_id=product_id,
                metadata={'product_name': product_name}
            )

            return Response({'message': 'Đã xóa sản phẩm khỏi giỏ hàng'})
        except CartItem.DoesNotExist:
            return Response({'error': 'Không tìm thấy sản phẩm trong giỏ hàng'}, status=status.HTTP_404_NOT_FOUND)


class CartClearView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart, _ = Cart.objects.get_or_create(user_id=request.user.id)
        cart.items.all().delete()
        return Response({'message': 'Đã xóa toàn bộ giỏ hàng'})
