from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .engine import chatbot_engine
from .models import Conversation, Message, FAQ, Intent


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
        message = request.data.get('message', '')
        conversation_id = request.data.get('conversation_id')
        session_id = request.data.get('session_id', request.session.session_key)

        # Get user_id from auth header if available
        user_id = None
        auth_header = request.headers.get('X-User-Id')
        if auth_header:
            user_id = auth_header

        if not message:
            return Response(
                {'error': 'Message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = chatbot_engine.chat_sync(
            message=message,
            conversation_id=conversation_id,
            session_id=session_id,
            user_id=user_id
        )

        return Response(result)


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
