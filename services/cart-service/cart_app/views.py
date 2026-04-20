import httpx
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer


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

        return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def put(self, request, pk):
        cart, _ = Cart.objects.get_or_create(user_id=request.user.id)
        try:
            item = CartItem.objects.get(pk=pk, cart=cart)
        except CartItem.DoesNotExist:
            return Response({'error': 'Không tìm thấy sản phẩm trong giỏ hàng'}, status=status.HTTP_404_NOT_FOUND)

        quantity = int(request.data.get('quantity', item.quantity))
        if quantity <= 0:
            item.delete()
            return Response({'message': 'Đã xóa sản phẩm khỏi giỏ hàng'})

        item.quantity = quantity
        item.save()
        return Response(CartItemSerializer(item).data)

    def delete(self, request, pk):
        cart, _ = Cart.objects.get_or_create(user_id=request.user.id)
        try:
            item = CartItem.objects.get(pk=pk, cart=cart)
            item.delete()
            return Response({'message': 'Đã xóa sản phẩm khỏi giỏ hàng'})
        except CartItem.DoesNotExist:
            return Response({'error': 'Không tìm thấy sản phẩm trong giỏ hàng'}, status=status.HTTP_404_NOT_FOUND)


class CartClearView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart, _ = Cart.objects.get_or_create(user_id=request.user.id)
        cart.items.all().delete()
        return Response({'message': 'Đã xóa toàn bộ giỏ hàng'})
