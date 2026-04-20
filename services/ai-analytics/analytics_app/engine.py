"""
AI Analytics Engine with Sales Prediction
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
import numpy as np
from django.db.models import Sum, Avg, Count, F
from django.db.models.functions import TruncDate
from django.core.cache import cache
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """
    Analytics Engine với:
    1. Dashboard metrics
    2. Sales reporting
    3. Sales prediction (Linear Regression)
    4. Customer segmentation (RFM Analysis)
    5. Trend analysis
    """

    MODEL_VERSION = "v1.0"

    def get_dashboard_metrics(self, days=30):
        """Lấy metrics cho dashboard"""
        from .models import DailySales

        cache_key = f"dashboard_metrics:{days}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # Current period
        current_stats = DailySales.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(
            total_revenue=Sum('total_revenue'),
            total_orders=Sum('total_orders'),
            total_items=Sum('total_items'),
            avg_order_value=Avg('avg_order_value'),
            new_customers=Sum('new_customers'),
        )

        # Previous period for comparison
        prev_start = start_date - timedelta(days=days)
        prev_end = start_date - timedelta(days=1)

        prev_stats = DailySales.objects.filter(
            date__gte=prev_start,
            date__lte=prev_end
        ).aggregate(
            total_revenue=Sum('total_revenue'),
            total_orders=Sum('total_orders'),
        )

        # Calculate growth
        revenue_growth = self._calculate_growth(
            current_stats['total_revenue'],
            prev_stats['total_revenue']
        )
        order_growth = self._calculate_growth(
            current_stats['total_orders'],
            prev_stats['total_orders']
        )

        metrics = {
            'period': f'{days} days',
            'total_revenue': float(current_stats['total_revenue'] or 0),
            'total_orders': current_stats['total_orders'] or 0,
            'total_items': current_stats['total_items'] or 0,
            'avg_order_value': float(current_stats['avg_order_value'] or 0),
            'new_customers': current_stats['new_customers'] or 0,
            'revenue_growth': revenue_growth,
            'order_growth': order_growth,
        }

        cache.set(cache_key, metrics, timeout=300)
        return metrics

    def get_sales_report(self, start_date, end_date, group_by='day'):
        """Báo cáo doanh số"""
        from .models import DailySales

        sales = DailySales.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')

        if group_by == 'week':
            # Group by week
            from django.db.models.functions import TruncWeek
            sales = sales.annotate(
                period=TruncWeek('date')
            ).values('period').annotate(
                revenue=Sum('total_revenue'),
                orders=Sum('total_orders'),
                items=Sum('total_items')
            ).order_by('period')
        elif group_by == 'month':
            from django.db.models.functions import TruncMonth
            sales = sales.annotate(
                period=TruncMonth('date')
            ).values('period').annotate(
                revenue=Sum('total_revenue'),
                orders=Sum('total_orders'),
                items=Sum('total_items')
            ).order_by('period')
        else:
            sales = sales.values('date').annotate(
                period=F('date'),
                revenue=F('total_revenue'),
                orders=F('total_orders'),
                items=F('total_items')
            )

        return {
            'start_date': str(start_date),
            'end_date': str(end_date),
            'group_by': group_by,
            'data': list(sales)
        }

    def get_product_analytics(self, product_id=None, days=30):
        """Phân tích sản phẩm"""
        from .models import ProductAnalytics

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        queryset = ProductAnalytics.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        )

        if product_id:
            queryset = queryset.filter(product_id=product_id)

        # Aggregate by product
        analytics = queryset.values('product_id').annotate(
            total_views=Sum('views'),
            total_add_to_carts=Sum('add_to_carts'),
            total_purchases=Sum('purchases'),
            total_revenue=Sum('revenue'),
            avg_conversion=Avg('conversion_rate')
        ).order_by('-total_revenue')[:20]

        return {
            'period_days': days,
            'products': list(analytics)
        }

    def predict_sales(self, days_ahead=7):
        """Dự đoán doanh số bằng Linear Regression"""
        from .models import DailySales, SalesPrediction

        cache_key = f"sales_prediction:{days_ahead}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Get historical data (last 90 days)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)

        historical = list(DailySales.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date').values('date', 'total_revenue', 'total_orders'))

        if len(historical) < 14:
            return {'error': 'Not enough historical data', 'predictions': []}

        # Prepare training data
        X = np.array(range(len(historical))).reshape(-1, 1)
        y_revenue = np.array([float(h['total_revenue']) for h in historical])
        y_orders = np.array([h['total_orders'] for h in historical])

        # Train models
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        revenue_model = LinearRegression()
        revenue_model.fit(X_scaled, y_revenue)

        orders_model = LinearRegression()
        orders_model.fit(X_scaled, y_orders)

        # Predict future
        predictions = []
        for i in range(1, days_ahead + 1):
            future_day = len(historical) + i - 1
            X_future = scaler.transform([[future_day]])

            predicted_revenue = max(0, revenue_model.predict(X_future)[0])
            predicted_orders = max(0, int(orders_model.predict(X_future)[0]))

            pred_date = end_date + timedelta(days=i)

            # Calculate confidence based on R2 score
            r2 = revenue_model.score(X_scaled, y_revenue)
            confidence = min(0.95, max(0.5, r2))

            predictions.append({
                'date': str(pred_date),
                'predicted_revenue': round(predicted_revenue, 0),
                'predicted_orders': predicted_orders,
                'confidence': round(confidence, 2)
            })

            # Save prediction
            SalesPrediction.objects.update_or_create(
                date=pred_date,
                defaults={
                    'predicted_revenue': Decimal(str(round(predicted_revenue, 0))),
                    'predicted_orders': predicted_orders,
                    'confidence': confidence,
                    'model_version': self.MODEL_VERSION
                }
            )

        result = {
            'model_version': self.MODEL_VERSION,
            'generated_at': datetime.now().isoformat(),
            'predictions': predictions
        }

        cache.set(cache_key, result, timeout=3600)
        return result

    def segment_customers(self):
        """
        Phân khúc khách hàng bằng RFM Analysis
        R = Recency (ngày từ lần mua cuối)
        F = Frequency (số lần mua)
        M = Monetary (tổng chi tiêu)
        """
        from .models import CustomerSegment

        # This would typically fetch from order service
        # Here we'll work with existing segments
        segments = CustomerSegment.objects.values('segment').annotate(
            count=Count('id'),
            total_spent=Sum('total_spent'),
            avg_orders=Avg('total_orders')
        )

        segment_summary = {
            'vip': {'count': 0, 'description': 'High value, frequent buyers'},
            'loyal': {'count': 0, 'description': 'Regular buyers'},
            'regular': {'count': 0, 'description': 'Occasional buyers'},
            'new': {'count': 0, 'description': 'Recent first purchase'},
            'at_risk': {'count': 0, 'description': 'Previously active, now inactive'},
            'churned': {'count': 0, 'description': 'No activity for long time'},
        }

        for seg in segments:
            if seg['segment'] in segment_summary:
                segment_summary[seg['segment']]['count'] = seg['count']
                segment_summary[seg['segment']]['total_spent'] = float(seg['total_spent'] or 0)
                segment_summary[seg['segment']]['avg_orders'] = float(seg['avg_orders'] or 0)

        return segment_summary

    def get_trend_analysis(self, days=30):
        """Phân tích xu hướng"""
        from .models import DailySales, CategoryAnalytics

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # Revenue trend
        daily_revenue = list(DailySales.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date').values('date', 'total_revenue', 'total_orders'))

        # Calculate moving average
        revenues = [float(d['total_revenue']) for d in daily_revenue]
        if len(revenues) >= 7:
            moving_avg = []
            for i in range(len(revenues)):
                if i < 6:
                    moving_avg.append(revenues[i])
                else:
                    avg = sum(revenues[i-6:i+1]) / 7
                    moving_avg.append(round(avg, 0))
        else:
            moving_avg = revenues

        # Category trends
        category_trends = CategoryAnalytics.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).values('category').annotate(
            total_revenue=Sum('total_revenue'),
            total_sales=Sum('total_sales')
        ).order_by('-total_revenue')[:10]

        # Detect trend direction
        if len(revenues) >= 14:
            first_half = sum(revenues[:len(revenues)//2])
            second_half = sum(revenues[len(revenues)//2:])
            if second_half > first_half * 1.1:
                trend_direction = 'increasing'
            elif second_half < first_half * 0.9:
                trend_direction = 'decreasing'
            else:
                trend_direction = 'stable'
        else:
            trend_direction = 'insufficient_data'

        return {
            'period_days': days,
            'trend_direction': trend_direction,
            'daily_data': [
                {
                    'date': str(d['date']),
                    'revenue': float(d['total_revenue']),
                    'orders': d['total_orders'],
                    'moving_avg': moving_avg[i] if i < len(moving_avg) else None
                }
                for i, d in enumerate(daily_revenue)
            ],
            'category_trends': list(category_trends)
        }

    def _calculate_growth(self, current, previous):
        """Tính tỷ lệ tăng trưởng"""
        if not previous or previous == 0:
            return 0
        current = float(current or 0)
        previous = float(previous)
        return round(((current - previous) / previous) * 100, 2)

    def record_daily_sales(self, date, orders_data):
        """Ghi nhận doanh số hàng ngày (được gọi từ cron job)"""
        from .models import DailySales

        total_revenue = sum(o.get('total', 0) for o in orders_data)
        total_items = sum(o.get('items_count', 0) for o in orders_data)
        total_orders = len(orders_data)

        # Count unique customers
        customer_ids = set(o.get('user_id') for o in orders_data if o.get('user_id'))
        # This is simplified - real impl would check if customer is new

        DailySales.objects.update_or_create(
            date=date,
            defaults={
                'total_orders': total_orders,
                'total_revenue': Decimal(str(total_revenue)),
                'total_items': total_items,
                'avg_order_value': Decimal(str(total_revenue / total_orders)) if total_orders > 0 else 0,
            }
        )


# Singleton
analytics_engine = AnalyticsEngine()
