from django.db.models import Avg, Count
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Review
from .serializers import ReviewSerializer

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
        reviews = Review.objects.filter(is_visible=True).prefetch_related('images', 'replies')[:50]
        return Response(ReviewSerializer(reviews, many=True).data)

    def post(self, request):
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user_id=request.user.id)
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
