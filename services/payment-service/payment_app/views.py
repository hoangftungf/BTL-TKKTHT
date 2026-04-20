import uuid
import hmac
import hashlib
import json
from urllib.parse import urlencode
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Payment
from .serializers import PaymentSerializer, CreatePaymentSerializer


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'healthy', 'service': 'payment-service'})


class MoMoPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreatePaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        transaction_id = f"MOMO{timezone.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:8].upper()}"

        payment = Payment.objects.create(
            order_id=data['order_id'],
            user_id=request.user.id,
            transaction_id=transaction_id,
            method='momo',
            amount=data['amount'],
            return_url=data.get('return_url', ''),
            status='pending'
        )

        # MoMo payment URL (sandbox)
        payment_url = f"{settings.MOMO_ENDPOINT}/create?orderId={transaction_id}&amount={int(data['amount'])}"
        payment.payment_url = payment_url
        payment.save()

        return Response({
            'payment': PaymentSerializer(payment).data,
            'payment_url': payment_url
        }, status=status.HTTP_201_CREATED)


class VNPayPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreatePaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        transaction_id = f"VNPAY{timezone.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:8].upper()}"

        payment = Payment.objects.create(
            order_id=data['order_id'],
            user_id=request.user.id,
            transaction_id=transaction_id,
            method='vnpay',
            amount=data['amount'],
            return_url=data.get('return_url', ''),
            status='pending'
        )

        # VNPay payment URL (sandbox)
        params = {
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_TmnCode': settings.VNPAY_TMN_CODE,
            'vnp_Amount': int(data['amount']) * 100,
            'vnp_CreateDate': timezone.now().strftime('%Y%m%d%H%M%S'),
            'vnp_CurrCode': 'VND',
            'vnp_IpAddr': request.META.get('REMOTE_ADDR', '127.0.0.1'),
            'vnp_Locale': 'vn',
            'vnp_OrderInfo': f'Thanh toan don hang {transaction_id}',
            'vnp_OrderType': 'other',
            'vnp_ReturnUrl': data.get('return_url', 'http://localhost:3000/payment/return'),
            'vnp_TxnRef': transaction_id,
        }

        sorted_params = sorted(params.items())
        query_string = urlencode(sorted_params)
        hash_data = settings.VNPAY_HASH_SECRET + '|' + query_string
        secure_hash = hmac.new(settings.VNPAY_HASH_SECRET.encode(), query_string.encode(), hashlib.sha512).hexdigest()

        payment_url = f"{settings.VNPAY_URL}?{query_string}&vnp_SecureHash={secure_hash}"
        payment.payment_url = payment_url
        payment.save()

        return Response({
            'payment': PaymentSerializer(payment).data,
            'payment_url': payment_url
        }, status=status.HTTP_201_CREATED)


class CODPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreatePaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        transaction_id = f"COD{timezone.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:8].upper()}"

        payment = Payment.objects.create(
            order_id=data['order_id'],
            user_id=request.user.id,
            transaction_id=transaction_id,
            method='cod',
            amount=data['amount'],
            status='pending'
        )

        return Response({
            'payment': PaymentSerializer(payment).data,
            'message': 'Đơn hàng sẽ được thanh toán khi nhận hàng'
        }, status=status.HTTP_201_CREATED)


class PaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            payment = Payment.objects.filter(order_id=order_id, user_id=request.user.id).latest('created_at')
            return Response(PaymentSerializer(payment).data)
        except Payment.DoesNotExist:
            return Response({'error': 'Không tìm thấy thanh toán'}, status=status.HTTP_404_NOT_FOUND)


class MoMoWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        order_id = data.get('orderId')
        result_code = data.get('resultCode')

        try:
            payment = Payment.objects.get(transaction_id=order_id)
            if result_code == 0:
                payment.status = 'completed'
                payment.paid_at = timezone.now()
                payment.provider_transaction_id = data.get('transId', '')
            else:
                payment.status = 'failed'
            payment.provider_response = data
            payment.save()
            return Response({'message': 'OK'})
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)


class VNPayReturnView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        vnp_ResponseCode = request.query_params.get('vnp_ResponseCode')
        vnp_TxnRef = request.query_params.get('vnp_TxnRef')

        try:
            payment = Payment.objects.get(transaction_id=vnp_TxnRef)
            if vnp_ResponseCode == '00':
                payment.status = 'completed'
                payment.paid_at = timezone.now()
                payment.provider_transaction_id = request.query_params.get('vnp_TransactionNo', '')
            else:
                payment.status = 'failed'
            payment.provider_response = dict(request.query_params)
            payment.save()
            return Response({'status': payment.status, 'transaction_id': vnp_TxnRef})
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
