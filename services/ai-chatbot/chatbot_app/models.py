import uuid
from django.db import models


class Conversation(models.Model):
    """Cuộc hội thoại với chatbot"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True, null=True, blank=True)
    session_id = models.CharField(max_length=100, db_index=True)
    context = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'conversations'
        ordering = ['-updated_at']


class Message(models.Model):
    """Tin nhắn trong cuộc hội thoại"""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']


class Intent(models.Model):
    """Ý định của người dùng"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    patterns = models.JSONField(default=list)  # Các mẫu câu
    responses = models.JSONField(default=list)  # Các câu trả lời mẫu
    action = models.CharField(max_length=100, blank=True)  # Action handler
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'intents'

    def __str__(self):
        return self.name


class FAQ(models.Model):
    """Câu hỏi thường gặp"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=100, blank=True)
    keywords = models.TextField(blank=True)
    view_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'faqs'
        ordering = ['-view_count']

    def __str__(self):
        return self.question[:50]
