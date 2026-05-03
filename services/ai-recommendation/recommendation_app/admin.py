from django.contrib import admin
from .models import UserBehavior, UserInteraction, ProductSimilarity, UserRecommendation


@admin.register(UserBehavior)
class UserBehaviorAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'product_id', 'action', 'search_query', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user_id', 'product_id', 'search_query')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'product_id', 'interaction_type', 'score', 'created_at')
    list_filter = ('interaction_type',)
    search_fields = ('user_id', 'product_id')

@admin.register(ProductSimilarity)
class ProductSimilarityAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'similar_product_id', 'similarity_score', 'updated_at')
    search_fields = ('product_id', 'similar_product_id')

@admin.register(UserRecommendation)
class UserRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'product_id', 'score', 'reason', 'updated_at')
    search_fields = ('user_id', 'product_id')
