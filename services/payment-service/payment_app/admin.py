from django.contrib import admin
from .models import Payment, Refund

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'order_id', 'method', 'amount', 'status', 'paid_at', 'created_at')
    list_filter = ('status', 'method')
    search_fields = ('transaction_id', 'order_id', 'provider_transaction_id')
    readonly_fields = ('transaction_id', 'created_at', 'updated_at')

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('refund_id', 'payment', 'amount', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('refund_id',)
