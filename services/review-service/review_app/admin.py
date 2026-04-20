from django.contrib import admin
from .models import Review, ReviewImage, ReviewReply

class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 0

class ReviewReplyInline(admin.TabularInline):
    model = ReviewReply
    extra = 0

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'user_id', 'rating', 'is_verified', 'is_visible', 'created_at')
    list_filter = ('rating', 'is_verified', 'is_visible')
    search_fields = ('product_id', 'user_id', 'content')
    inlines = [ReviewImageInline, ReviewReplyInline]
