from django.urls import path
from .views import (
    HealthCheckView,
    ChatView,
    ConversationView,
    FAQListView,
    IntentListView,
)

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health'),
    path('chat/', ChatView.as_view(), name='chat'),
    path('conversations/<uuid:conversation_id>/', ConversationView.as_view(), name='conversation'),
    path('faqs/', FAQListView.as_view(), name='faq-list'),
    path('intents/', IntentListView.as_view(), name='intent-list'),
]
