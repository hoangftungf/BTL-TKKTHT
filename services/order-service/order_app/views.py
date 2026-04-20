import httpx
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Order, OrderItem, OrderStatusHistory
from .serializers import OrderListSerializer, OrderDetailSerializer, CreateOrderSerializer


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'healthy', 'service': 'order-service'})


class OrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user_id=request.user.id).prefetch_related('items')
        status_filter = request.query_params.get('status')
        if status_filter:
            orders = orders.filter(status=status_filter)
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            headers = {'Authorization': request.headers.get('Authorization')}
            cart_response = httpx.get(f"{settings.CART_SERVICE_URL}/", headers=headers, timeout=10.0)
            if cart_response.status_code != 200:
                return Response({'error': 'Không thể lấy thông tin giỏ hàng'}, status=status.HTTP_400_BAD_REQUEST)
            cart_data = cart_response.json()
        except Exception as e:
            return Response({'error': f'Lỗi kết nối: {str(e)}'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if not cart_data.get('items'):
            return Response({'error': 'Giỏ hàng trống'}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        subtotal = float(cart_data.get('total_amount', 0) or 0)
        shipping_fee = 30000

        order = Order.objects.create(
            user_id=request.user.id,
            recipient_name=data['recipient_name'],
            recipient_phone=data['recipient_phone'],
            shipping_address=data['shipping_address'],
            shipping_province=data['shipping_province'],
            shipping_district=data['shipping_district'],
            shipping_ward=data['shipping_ward'],
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            total_amount=subtotal + shipping_fee,
            payment_method=data['payment_method'],
            note=data.get('note', ''),
        )

        for item in cart_data.get('items', []):
            OrderItem.objects.create(
                order=order,
                product_id=item['product_id'],
                variant_id=item.get('variant_id'),
                product_name=item['product_name'],
                product_image=item.get('product_image', ''),
                sku=item.get('sku', ''),
                price=item['price'],
                quantity=item['quantity'],
                subtotal=item['subtotal'],
            )

        OrderStatusHistory.objects.create(order=order, status='pending', note='Đơn hàng mới được tạo')

        try:
            httpx.delete(f"{settings.CART_SERVICE_URL}/clear/", headers=headers, timeout=5.0)
        except Exception:
            pass

        return Response(OrderDetailSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            order = Order.objects.prefetch_related('items', 'status_history').get(pk=pk, user_id=request.user.id)
            return Response(OrderDetailSerializer(order).data)
        except Order.DoesNotExist:
            return Response({'error': 'Đơn hàng không tồn tại'}, status=status.HTTP_404_NOT_FOUND)


class OrderCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, user_id=request.user.id)
        except Order.DoesNotExist:
            return Response({'error': 'Đơn hàng không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

        if order.status not in ['pending', 'confirmed']:
            return Response({'error': 'Không thể hủy đơn hàng ở trạng thái này'}, status=status.HTTP_400_BAD_REQUEST)

        reason = request.data.get('reason', '')
        order.status = 'cancelled'
        order.cancel_reason = reason
        order.save()

        OrderStatusHistory.objects.create(order=order, status='cancelled', note=reason, created_by=request.user.id)

        return Response({'message': 'Đã hủy đơn hàng', 'order': OrderDetailSerializer(order).data})


class OrderTrackView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            order = Order.objects.prefetch_related('status_history').get(pk=pk, user_id=request.user.id)
            return Response({
                'order_number': order.order_number,
                'status': order.status,
                'status_display': order.get_status_display(),
                'history': [
                    {'status': h.status, 'status_display': dict(Order.STATUS_CHOICES).get(h.status, h.status), 'note': h.note, 'created_at': h.created_at}
                    for h in order.status_history.all()
                ]
            })
        except Order.DoesNotExist:
            return Response({'error': 'Đơn hàng không tồn tại'}, status=status.HTTP_404_NOT_FOUND)
