from rest_framework import serializers
from .models import Payment, Refund


class PaymentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    method_display = serializers.CharField(source='get_method_display', read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'order_id', 'transaction_id', 'method', 'method_display', 'amount', 'currency',
                  'status', 'status_display', 'payment_url', 'paid_at', 'created_at']


class CreatePaymentSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=0)
    return_url = serializers.URLField(required=False)


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ['id', 'refund_id', 'amount', 'reason', 'status', 'created_at', 'completed_at']
