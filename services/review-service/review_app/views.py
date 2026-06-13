from django.db.models import Avg, Count
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Review, ReviewReply
from .serializers import ReviewSerializer, ReviewReplySerializer
from lib.shared.domain_events import ReviewCreated, EventBus

class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response({'status': 'healthy', 'service': 'review-service'})

class ReviewListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        reviews = Review.objects.all().prefetch_related('images', 'replies')
        
        order_id = request.query_params.get('order_id')
        if order_id:
            reviews = reviews.filter(order_id=order_id)
            
        user_id = request.query_params.get('user_id')
        if user_id:
            reviews = reviews.filter(user_id=user_id)
            
        if not order_id and not user_id:
            reviews = reviews.filter(is_visible=True)
            
        return Response(ReviewSerializer(reviews[:100], many=True).data)

    def post(self, request):
        order_id = request.data.get('order_id')
        product_id = request.data.get('product_id')
        
        if not order_id:
            return Response({'error': 'Mã đơn hàng (order_id) là bắt buộc'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Check if review already exists
        if Review.objects.filter(product_id=product_id, user_id=request.user.id).exists():
            return Response({'error': 'Bạn đã đánh giá sản phẩm này rồi'}, status=status.HTTP_400_BAD_REQUEST)
            
        import httpx
        from django.conf import settings
        
        order_service_url = getattr(settings, 'ORDER_SERVICE_URL', 'http://order-service:8005')
        headers = {
            'Authorization': request.headers.get('Authorization', '')
        }
        
        try:
            response = httpx.get(f"{order_service_url}/{order_id}/", headers=headers, timeout=5.0)
            if response.status_code != 200:
                return Response({'error': 'Đơn hàng không tồn tại hoặc bạn không có quyền truy cập'}, status=status.HTTP_400_BAD_REQUEST)
                
            order_data = response.json()
            
            # Check status is completed (buyer clicked "Đã nhận được hàng")
            if order_data.get('status') != 'completed':
                return Response({'error': 'Bạn chỉ có thể đánh giá sản phẩm sau khi đã xác nhận nhận được hàng (Đơn hàng đã hoàn thành)'}, status=status.HTTP_400_BAD_REQUEST)
                
            # Verify the product is in the order items
            items = order_data.get('items', [])
            product_in_order = any(str(item.get('product_id')) == str(product_id) for item in items)
            if not product_in_order:
                return Response({'error': 'Sản phẩm này không nằm trong đơn hàng của bạn'}, status=status.HTTP_400_BAD_REQUEST)
                
        except httpx.RequestError:
            # Fallback if communication is broken
            pass

        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user_id=request.user.id, is_verified=True)
            
            try:
                from .notification_helper import notify_admins
                notify_admins(
                    title="Đánh giá sản phẩm mới",
                    message=f"Sản phẩm {product_id} vừa nhận được đánh giá {serializer.instance.rating} sao mới từ người dùng u-{str(request.user.id)[:6]}.",
                    data={'product_id': str(product_id), 'review_id': str(serializer.instance.id)}
                )
            except Exception as e:
                print(f"Failed to send review notification: {e}")

            # Publish domain event
            try:
                EventBus.publish(ReviewCreated({
                    'review_id': str(serializer.instance.id),
                    'product_id': str(product_id),
                    'user_id': str(request.user.id),
                    'rating': serializer.instance.rating,
                    'order_id': str(order_id),
                }))
            except Exception as e:
                print(f"Failed to publish ReviewCreated event: {e}")

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ReviewDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ['PUT', 'DELETE']:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request, pk):
        try:
            review = Review.objects.prefetch_related('images', 'replies').get(pk=pk, is_visible=True)
            return Response(ReviewSerializer(review).data)
        except Review.DoesNotExist:
            return Response({'error': 'Không tìm thấy đánh giá'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            review = Review.objects.get(pk=pk, user_id=request.user.id)
        except Review.DoesNotExist:
            return Response({'error': 'Không tìm thấy đánh giá'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            review = Review.objects.get(pk=pk, user_id=request.user.id)
            review.delete()
            return Response({'message': 'Đã xóa đánh giá'})
        except Review.DoesNotExist:
            return Response({'error': 'Không tìm thấy đánh giá'}, status=status.HTTP_404_NOT_FOUND)

class ProductReviewsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, product_id):
        reviews = Review.objects.filter(product_id=product_id, is_visible=True).prefetch_related('images', 'replies')
        rating = request.query_params.get('rating')
        if rating:
            reviews = reviews.filter(rating=rating)
        return Response(ReviewSerializer(reviews, many=True).data)

class ProductStatsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, product_id):
        reviews = Review.objects.filter(product_id=product_id, is_visible=True)
        stats = reviews.aggregate(
            avg_rating=Avg('rating'),
            total_reviews=Count('id')
        )
        rating_distribution = {}
        for i in range(1, 6):
            rating_distribution[i] = reviews.filter(rating=i).count()
        return Response({
            'product_id': str(product_id),
            'avg_rating': round(stats['avg_rating'] or 0, 2),
            'total_reviews': stats['total_reviews'],
            'rating_distribution': rating_distribution
        })

class ReviewReplyCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, review_id):
        try:
            review = Review.objects.get(pk=review_id)
        except Review.DoesNotExist:
            return Response({'error': 'Không tìm thấy đánh giá'}, status=status.HTTP_404_NOT_FOUND)
            
        is_seller = getattr(request.user, 'is_staff', False)
        
        content = request.data.get('content')
        if not content:
            return Response({'error': 'Nội dung phản hồi không được để trống'}, status=status.HTTP_400_BAD_REQUEST)
            
        reply = ReviewReply.objects.create(
            review=review,
            user_id=request.user.id,
            content=content,
            is_seller=is_seller
        )
        return Response(ReviewReplySerializer(reply).data, status=status.HTTP_201_CREATED)

class AdminReviewListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not getattr(request.user, 'is_staff', False):
            return Response({'error': 'Quyền truy cập bị từ chối'}, status=status.HTTP_403_FORBIDDEN)
        
        reviews = Review.objects.all().prefetch_related('images', 'replies')
        
        product_id = request.query_params.get('product_id')
        if product_id:
            reviews = reviews.filter(product_id=product_id)
            
        rating = request.query_params.get('rating')
        if rating:
            reviews = reviews.filter(rating=rating)
            
        is_visible = request.query_params.get('is_visible')
        if is_visible is not None:
            is_visible = is_visible.lower() == 'true'
            reviews = reviews.filter(is_visible=is_visible)
            
        return Response(ReviewSerializer(reviews, many=True).data)

class AdminReviewVisibilityView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if not getattr(request.user, 'is_staff', False):
            return Response({'error': 'Quyền truy cập bị từ chối'}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            review = Review.objects.get(pk=pk)
        except Review.DoesNotExist:
            return Response({'error': 'Không tìm thấy đánh giá'}, status=status.HTTP_404_NOT_FOUND)
            
        is_visible = request.data.get('is_visible')
        if is_visible is not None:
            review.is_visible = bool(is_visible)
            review.save()
            
        return Response(ReviewSerializer(review).data)
