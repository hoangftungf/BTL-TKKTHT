from datetime import datetime, timedelta
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .engine import analytics_engine
from .models import DailySales, ProductAnalytics, CustomerSegment


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'ai-analytics'
        })


class DashboardView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Lấy metrics cho dashboard"""
        days = int(request.query_params.get('days', 30))
        metrics = analytics_engine.get_dashboard_metrics(days=days)
        return Response(metrics)


class SalesReportView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Báo cáo doanh số"""
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        group_by = request.query_params.get('group_by', 'day')

        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            start_date = datetime.now().date() - timedelta(days=30)

        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            end_date = datetime.now().date()

        report = analytics_engine.get_sales_report(
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )
        return Response(report)

    def post(self, request):
        """Ghi nhận doanh số (internal API)"""
        date_str = request.data.get('date')
        orders_data = request.data.get('orders', [])

        if not date_str:
            return Response(
                {'error': 'date is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        analytics_engine.record_daily_sales(date, orders_data)

        return Response({'status': 'recorded'})


class ProductAnalyticsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Phân tích sản phẩm"""
        product_id = request.query_params.get('product_id')
        days = int(request.query_params.get('days', 30))

        analytics = analytics_engine.get_product_analytics(
            product_id=product_id,
            days=days
        )
        return Response(analytics)

    def post(self, request):
        """Ghi nhận analytics sản phẩm"""
        product_id = request.data.get('product_id')
        event_type = request.data.get('event_type')  # view, add_to_cart, purchase

        if not product_id or not event_type:
            return Response(
                {'error': 'product_id and event_type required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        today = datetime.now().date()
        analytics, _ = ProductAnalytics.objects.get_or_create(
            product_id=product_id,
            date=today,
            defaults={}
        )

        if event_type == 'view':
            analytics.views += 1
        elif event_type == 'add_to_cart':
            analytics.add_to_carts += 1
        elif event_type == 'purchase':
            analytics.purchases += 1
            revenue = request.data.get('revenue', 0)
            analytics.revenue += revenue

        # Update conversion rate
        if analytics.views > 0:
            analytics.conversion_rate = analytics.purchases / analytics.views

        analytics.save()

        return Response({'status': 'recorded'})


class SalesPredictionView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Dự đoán doanh số"""
        days_ahead = int(request.query_params.get('days', 7))
        predictions = analytics_engine.predict_sales(days_ahead=days_ahead)
        return Response(predictions)


class CustomerSegmentView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Phân khúc khách hàng"""
        segments = analytics_engine.segment_customers()
        return Response({
            'segments': segments,
            'total_customers': CustomerSegment.objects.count()
        })

    def post(self, request):
        """Cập nhật segment cho customer"""
        user_id = request.data.get('user_id')
        segment_data = request.data.get('data', {})

        if not user_id:
            return Response(
                {'error': 'user_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate RFM score
        rfm_score = (
            segment_data.get('recency_score', 0) * 0.3 +
            segment_data.get('frequency_score', 0) * 0.3 +
            segment_data.get('monetary_score', 0) * 0.4
        )

        # Determine segment based on RFM
        if rfm_score >= 8:
            segment = 'vip'
        elif rfm_score >= 6:
            segment = 'loyal'
        elif rfm_score >= 4:
            segment = 'regular'
        elif segment_data.get('days_since_last_order', 0) > 90:
            segment = 'churned'
        elif segment_data.get('days_since_last_order', 0) > 30:
            segment = 'at_risk'
        else:
            segment = 'new'

        CustomerSegment.objects.update_or_create(
            user_id=user_id,
            defaults={
                'segment': segment,
                'total_orders': segment_data.get('total_orders', 0),
                'total_spent': segment_data.get('total_spent', 0),
                'avg_order_value': segment_data.get('avg_order_value', 0),
                'days_since_last_order': segment_data.get('days_since_last_order', 0),
                'rfm_score': rfm_score
            }
        )

        return Response({'segment': segment, 'rfm_score': rfm_score})


class TrendAnalysisView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Phân tích xu hướng"""
        days = int(request.query_params.get('days', 30))
        trends = analytics_engine.get_trend_analysis(days=days)
        return Response(trends)
