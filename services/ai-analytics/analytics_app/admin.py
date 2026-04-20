from django.contrib import admin
from .models import DailySales, ProductAnalytics, CategoryAnalytics, SalesPrediction, CustomerSegment


@admin.register(DailySales)
class DailySalesAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_orders', 'total_revenue', 'avg_order_value', 'new_customers')
    list_filter = ('date',)
    ordering = ('-date',)


@admin.register(ProductAnalytics)
class ProductAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'date', 'views', 'purchases', 'revenue', 'conversion_rate')
    list_filter = ('date',)
    search_fields = ('product_id',)


@admin.register(CategoryAnalytics)
class CategoryAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('category', 'date', 'total_sales', 'total_revenue')
    list_filter = ('category', 'date')


@admin.register(SalesPrediction)
class SalesPredictionAdmin(admin.ModelAdmin):
    list_display = ('date', 'predicted_revenue', 'predicted_orders', 'confidence', 'model_version')
    list_filter = ('model_version',)
    ordering = ('-date',)


@admin.register(CustomerSegment)
class CustomerSegmentAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'segment', 'total_orders', 'total_spent', 'rfm_score')
    list_filter = ('segment',)
    search_fields = ('user_id',)
