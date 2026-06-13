from django.urls import path
from .views import (
    HealthCheckView,
    MetricsView,
    ChatView,
    ChatStreamView,
    RateMessageView,
    UpdateProductView,
    AuditChatQualityView,
    ConversationView,
    ConversationListView,
    FAQListView,
    IntentListView,
)

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health'),
    path('metrics/', MetricsView.as_view(), name='metrics'),
    path('chat/', ChatView.as_view(), name='chat'),
    path('chat/stream/', ChatStreamView.as_view(), name='chat-stream'),
    path('messages/<uuid:message_id>/rate/', RateMessageView.as_view(), name='rate-message'),
    path('update-product/', UpdateProductView.as_view(), name='update-product'),
    path('audit-quality/', AuditChatQualityView.as_view(), name='audit-quality'),
    path('conversations/', ConversationListView.as_view(), name='conversations-list'),
    path('conversations/<uuid:conversation_id>/', ConversationView.as_view(), name='conversation'),
    path('faqs/', FAQListView.as_view(), name='faq-list'),
    path('intents/', IntentListView.as_view(), name='intent-list'),
]

