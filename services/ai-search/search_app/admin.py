from django.contrib import admin
from .models import ProductIndex, SearchHistory, Synonym

@admin.register(ProductIndex)
class ProductIndexAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'price', 'popularity_score', 'updated_at')
    search_fields = ('name', 'category', 'brand')
    list_filter = ('category', 'brand')

@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('query', 'search_count', 'result_count', 'updated_at')
    search_fields = ('query',)
    ordering = ('-search_count',)

@admin.register(Synonym)
class SynonymAdmin(admin.ModelAdmin):
    list_display = ('word', 'synonyms', 'created_at')
    search_fields = ('word',)
