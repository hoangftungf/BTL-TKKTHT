from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Shipment
from .serializers import ShipmentSerializer

class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response({'status': 'healthy', 'service': 'shipping-service'})

class ShipmentListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        order_id = request.query_params.get('order_id')
        if order_id:
            shipments = Shipment.objects.filter(order_id=order_id)
        else:
            shipments = Shipment.objects.all()[:50]
        return Response(ShipmentSerializer(shipments, many=True).data)

class ShipmentDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        try:
            shipment = Shipment.objects.prefetch_related('events').get(pk=pk)
            return Response(ShipmentSerializer(shipment).data)
        except Shipment.DoesNotExist:
            return Response({'error': 'Không tìm thấy đơn vận chuyển'}, status=status.HTTP_404_NOT_FOUND)

class TrackingView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, tracking_number):
        try:
            shipment = Shipment.objects.prefetch_related('events').get(tracking_number=tracking_number)
            return Response(ShipmentSerializer(shipment).data)
        except Shipment.DoesNotExist:
            return Response({'error': 'Không tìm thấy mã vận đơn'}, status=status.HTTP_404_NOT_FOUND)

class ShippingRateView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        province = request.data.get('province', '')
        weight = float(request.data.get('weight', 1))
        base_fee = 30000
        if province.lower() in ['hà nội', 'hồ chí minh']:
            base_fee = 20000
        weight_fee = max(0, (weight - 1) * 5000)
        total = base_fee + weight_fee
        return Response({
            'province': province,
            'weight': weight,
            'shipping_fee': total,
            'estimated_days': 3 if province.lower() in ['hà nội', 'hồ chí minh'] else 5
        })
