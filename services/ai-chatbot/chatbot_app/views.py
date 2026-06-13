from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.http import StreamingHttpResponse, HttpResponse
import json
import logging
import threading
from .engine import chatbot_engine
from .models import Conversation, Message, FAQ, Intent
from .metrics import metrics

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prometheus Metrics Endpoint
# ---------------------------------------------------------------------------

class MetricsView(APIView):
    """Expose Prometheus metrics for scraping."""
    permission_classes = [AllowAny]

    def get(self, request):
        from prometheus_client import generate_latest, REGISTRY
        return HttpResponse(
            generate_latest(REGISTRY),
            content_type='text/plain; charset=utf-8',
        )


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'ai-chatbot'
        })


class ChatView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Xử lý tin nhắn chat"""
        import time
        t0 = time.perf_counter()

        message = request.data.get('message', '')
        conversation_id = request.data.get('conversation_id')
        session_id = request.data.get('session_id', request.session.session_key)

        # Get user_id from auth header if available
        user_id = None
        auth_header = request.headers.get('X-User-Id')
        if auth_header:
            user_id = auth_header

        if not message:
            metrics.requests_total.labels(intent='chat', status='error').inc()
            return Response(
                {'error': 'Message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = chatbot_engine.chat_sync(
                message=message,
                conversation_id=conversation_id,
                session_id=session_id,
                user_id=user_id
            )
            metrics.requests_total.labels(intent='chat', status='success').inc()
            metrics.latency_seconds.labels(intent='chat').observe(time.perf_counter() - t0)
            return Response(result)
        except Exception as e:
            metrics.requests_total.labels(intent='chat', status='error').inc()
            metrics.errors_total.labels(error_type=type(e).__name__).inc()
            raise


class ChatStreamView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Xử lý tin nhắn chat dưới dạng stream (SSE)"""
        message = request.data.get('message', '')
        conversation_id = request.data.get('conversation_id')
        session_id = request.data.get('session_id', request.session.session_key)

        user_id = None
        auth_header = request.headers.get('X-User-Id')
        if auth_header:
            user_id = auth_header

        if not message:
            return Response(
                {'error': 'Message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        def event_stream():
            try:
                for chunk in chatbot_engine.chat_stream(
                    message=message,
                    conversation_id=conversation_id,
                    session_id=session_id,
                    user_id=user_id
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as exc:
                logger.error(f"Error in stream generator: {exc}")
                yield f"data: {json.dumps({'error': str(exc)})}\n\n"

        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        # Disable buffering for Nginx/proxies
        response['X-Accel-Buffering'] = 'no'
        response['Cache-Control'] = 'no-cache'
        return response


class RateMessageView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, message_id):
        """Đánh giá chất lượng tin nhắn của AI"""
        rating = request.data.get('rating')  # e.g., 1-5 or 'good'/'bad'
        feedback = request.data.get('feedback', '')

        if rating is None:
            return Response({'error': 'Rating is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            message = Message.objects.get(id=message_id)
            if not isinstance(message.metadata, dict):
                message.metadata = {}
            message.metadata['rating'] = rating
            message.metadata['feedback'] = feedback
            message.save(update_fields=['metadata'])
            return Response({'status': 'success', 'message_id': message_id})
        except Message.DoesNotExist:
            return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)


class UpdateProductView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """Webhook cập nhật cơ sở tri thức sản phẩm (async)"""
        product_data = request.data
        if not product_data or 'id' not in product_data:
            return Response({'error': 'Product data with id is required'}, status=status.HTTP_400_BAD_REQUEST)

        from .tasks import update_product_knowledge_base_async
        try:
            # Enqueue Celery task
            update_product_knowledge_base_async.delay(product_data)
            logger.info(f"Queued Celery task for product {product_data.get('id')}")
        except Exception as exc:
            # Fallback to local background thread if Celery/RabbitMQ is unavailable
            logger.warning(f"Celery failed, running async product update in background thread: {exc}")
            thread = threading.Thread(target=update_product_knowledge_base_async, args=(product_data,))
            thread.daemon = True
            thread.start()

        return Response({'status': 'queued', 'product_id': product_data.get('id')})


class AuditChatQualityView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Trích xuất danh sách hội thoại bị đánh giá thấp hoặc bỏ dở để audit"""
        limit = int(request.query_params.get('limit', 50))
        
        # 1. Rated poorly
        poor_messages = Message.objects.filter(role='assistant', metadata__rating__in=[1, 2, 'bad', 'poor']).order_by('-created_at')[:limit]
        
        # 2. Abandoned sessions (conversations with > 1 messages, no assistant rating but ended abruptly)
        # We can scan recent conversations
        conversations = Conversation.objects.all().order_by('-updated_at')[:limit]
        abandoned = []
        for c in conversations:
            msg_count = c.messages.count()
            # If conversation has messages, is older than 30 mins, and didn't result in positive action
            if msg_count > 1:
                last_msg = c.messages.last()
                # Check if last message was from user (abandoned)
                if last_msg and last_msg.role == 'user':
                    abandoned.append({
                        'conversation_id': str(c.id),
                        'updated_at': c.updated_at,
                        'message_count': msg_count,
                        'last_message': last_msg.content
                    })
                    
        return Response({
            'poorly_rated_chats': [
                {
                    'message_id': str(m.id),
                    'conversation_id': str(m.conversation.id),
                    'query': m.conversation.messages.filter(role='user', created_at__lt=m.created_at).last().content if m.conversation.messages.filter(role='user', created_at__lt=m.created_at).exists() else "",
                    'response': m.content,
                    'rating': m.metadata.get('rating'),
                    'feedback': m.metadata.get('feedback'),
                    'created_at': m.created_at
                }
                for m in poor_messages
            ],
            'abandoned_conversations': abandoned
        })


class ConversationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, conversation_id):
        """Lấy lịch sử hội thoại"""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            messages = conversation.messages.all()

            return Response({
                'conversation_id': str(conversation.id),
                'created_at': conversation.created_at,
                'messages': [
                    {
                        'id': str(m.id),
                        'role': m.role,
                        'content': m.content,
                        'created_at': m.created_at
                    }
                    for m in messages
                ]
            })
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def delete(self, request, conversation_id):
        """Xóa cuộc hội thoại"""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            conversation.delete()
            return Response({'status': 'deleted'})
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class FAQListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Danh sách FAQ"""
        category = request.query_params.get('category')

        faqs = FAQ.objects.filter(is_active=True)
        if category:
            faqs = faqs.filter(category=category)

        return Response({
            'faqs': [
                {
                    'id': str(f.id),
                    'question': f.question,
                    'answer': f.answer,
                    'category': f.category
                }
                for f in faqs[:20]
            ]
        })

    def post(self, request):
        """Thêm FAQ mới"""
        faq = FAQ.objects.create(
            question=request.data.get('question'),
            answer=request.data.get('answer'),
            category=request.data.get('category', ''),
            keywords=request.data.get('keywords', '')
        )
        return Response({
            'id': str(faq.id),
            'status': 'created'
        }, status=status.HTTP_201_CREATED)


class IntentListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """Danh sách intents"""
        intents = Intent.objects.all()
        return Response({
            'intents': [
                {
                    'id': str(i.id),
                    'name': i.name,
                    'patterns': i.patterns,
                    'action': i.action
                }
                for i in intents
            ]
        })


class ConversationListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        conversations = Conversation.objects.all().order_by('-created_at')[:50]
        return Response({
            'conversations': [
                {
                    'id': str(c.id),
                    'user_id': c.user_id,
                    'session_id': c.session_id,
                    'created_at': c.created_at,
                    'updated_at': c.updated_at,
                    'message_count': c.messages.count()
                }
                for c in conversations
            ]
        })
