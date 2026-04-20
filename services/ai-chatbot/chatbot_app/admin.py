from django.contrib import admin
from .models import Conversation, Message, Intent, FAQ


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'session_id', 'created_at', 'updated_at')
    search_fields = ('session_id',)
    list_filter = ('created_at',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('content',)


@admin.register(Intent)
class IntentAdmin(admin.ModelAdmin):
    list_display = ('name', 'action', 'created_at')
    search_fields = ('name',)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'view_count', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('question', 'answer')
