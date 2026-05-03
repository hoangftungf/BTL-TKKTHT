import logging
import httpx
import os
from threading import Thread
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Profile, Address, Wishlist
from .serializers import ProfileSerializer, AddressSerializer, WishlistSerializer

logger = logging.getLogger(__name__)


def track_behavior(user_id, action, product_id=None, metadata=None):
    """Send tracking request to recommendation service (async)."""
    if not user_id:
        return

    def _send():
        try:
            url = os.environ.get('RECOMMENDATION_SERVICE_URL', 'http://ai-recommendation:8000')
            payload = {
                'user_id': str(user_id),
                'action': action,
                'product_id': str(product_id) if product_id else None,
                'metadata': metadata or {},
            }
            httpx.post(f"{url}/track/", json=payload, timeout=5.0)
        except Exception as e:
            logger.warning(f"Tracking error: {e}")

    thread = Thread(target=_send)
    thread.daemon = True
    thread.start()


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'healthy', 'service': 'user-service'})


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, created = Profile.objects.get_or_create(user_id=request.user.id)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request):
        profile, created = Profile.objects.get_or_create(user_id=request.user.id)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddressListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        addresses = Address.objects.filter(user_id=request.user.id)
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user_id=request.user.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddressDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user_id):
        try:
            return Address.objects.get(pk=pk, user_id=user_id)
        except Address.DoesNotExist:
            return None

    def get(self, request, pk):
        address = self.get_object(pk, request.user.id)
        if not address:
            return Response({'error': 'Không tìm thấy địa chỉ'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AddressSerializer(address)
        return Response(serializer.data)

    def put(self, request, pk):
        address = self.get_object(pk, request.user.id)
        if not address:
            return Response({'error': 'Không tìm thấy địa chỉ'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AddressSerializer(address, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        address = self.get_object(pk, request.user.id)
        if not address:
            return Response({'error': 'Không tìm thấy địa chỉ'}, status=status.HTTP_404_NOT_FOUND)
        address.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wishlist = Wishlist.objects.filter(user_id=request.user.id)
        serializer = WishlistSerializer(wishlist, many=True)
        return Response(serializer.data)

    def post(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({'error': 'product_id là bắt buộc'}, status=status.HTTP_400_BAD_REQUEST)

        wishlist, created = Wishlist.objects.get_or_create(
            user_id=request.user.id,
            product_id=product_id
        )
        if created:
            # Track add_to_wishlist behavior
            track_behavior(
                user_id=request.user.id,
                action='add_to_wishlist',
                product_id=product_id,
            )
            return Response({'message': 'Đã thêm vào danh sách yêu thích'}, status=status.HTTP_201_CREATED)
        return Response({'message': 'Sản phẩm đã có trong danh sách yêu thích'})

    def delete(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({'error': 'product_id là bắt buộc'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            wishlist = Wishlist.objects.get(user_id=request.user.id, product_id=product_id)
            wishlist.delete()
            return Response({'message': 'Đã xóa khỏi danh sách yêu thích'})
        except Wishlist.DoesNotExist:
            return Response({'error': 'Không tìm thấy trong danh sách yêu thích'}, status=status.HTTP_404_NOT_FOUND)
