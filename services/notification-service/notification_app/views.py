from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer, SendNotificationSerializer

class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response({'status': 'healthy', 'service': 'notification-service'})

class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user_id=request.user.id)
        is_read = request.query_params.get('is_read')
        if is_read is not None:
            notifications = notifications.filter(is_read=is_read.lower() == 'true')
        type_filter = request.query_params.get('type')
        if type_filter:
            notifications = notifications.filter(type=type_filter)

        unread_count = Notification.objects.filter(user_id=request.user.id, is_read=False).count()
        return Response({
            'unread_count': unread_count,
            'notifications': NotificationSerializer(notifications[:50], many=True).data
        })

class NotificationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user_id=request.user.id)
            if not notification.is_read:
                notification.is_read = True
                notification.read_at = timezone.now()
                notification.save()
            return Response(NotificationSerializer(notification).data)
        except Notification.DoesNotExist:
            return Response({'error': 'Không tìm thấy thông báo'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user_id=request.user.id)
            notification.delete()
            return Response({'message': 'Đã xóa thông báo'})
        except Notification.DoesNotExist:
            return Response({'error': 'Không tìm thấy thông báo'}, status=status.HTTP_404_NOT_FOUND)

class MarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        notification_ids = request.data.get('ids', [])
        mark_all = request.data.get('all', False)

        if mark_all:
            Notification.objects.filter(user_id=request.user.id, is_read=False).update(
                is_read=True, read_at=timezone.now()
            )
            return Response({'message': 'Đã đánh dấu tất cả đã đọc'})

        if notification_ids:
            Notification.objects.filter(
                id__in=notification_ids, user_id=request.user.id, is_read=False
            ).update(is_read=True, read_at=timezone.now())
            return Response({'message': f'Đã đánh dấu {len(notification_ids)} thông báo đã đọc'})

        return Response({'error': 'Vui lòng cung cấp ids hoặc all=true'}, status=status.HTTP_400_BAD_REQUEST)

class SendNotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not getattr(request.user, 'is_staff', False):
            return Response({'error': 'Không có quyền'}, status=status.HTTP_403_FORBIDDEN)

        serializer = SendNotificationSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            notification = Notification.objects.create(
                user_id=data['user_id'],
                type=data['type'],
                channel=data['channel'],
                title=data['title'],
                message=data['message'],
                data=data.get('data', {})
            )
            return Response(NotificationSerializer(notification).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
