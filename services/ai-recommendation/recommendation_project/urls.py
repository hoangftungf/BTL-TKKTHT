from django.contrib import admin
from django.urls import path
from recommendation_app.views import (
    HealthCheckView,
    SimilarProductsView,
    PersonalizedRecommendationsView,
    TrendingProductsView,
    FrequentlyBoughtTogetherView,
    TrainModelView,
    RecordInteractionView,
    # Tracking
    TrackBehaviorView,
    BehaviorStatsView,
    # Hybrid Engine
    HybridRecommendationsView,
    HybridChatbotView,
    # LSTM
    LSTMPredictionsView,
    LSTMTrainView,
    # Knowledge Graph
    GraphRecommendationsView,
    GraphSimilarView,
    GraphSyncView,
    GraphStatsView,
    # RAG
    RAGSearchView,
    RAGIndexView,
    # Train All
    TrainAllModelsView,
    # Seed Data
    SeedDataView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', HealthCheckView.as_view()),

    # Legacy endpoints (Collaborative Filtering)
    path('product/<uuid:product_id>/', SimilarProductsView.as_view()),
    path('user/', PersonalizedRecommendationsView.as_view()),
    path('trending/', TrendingProductsView.as_view()),
    path('frequently-bought/<uuid:product_id>/', FrequentlyBoughtTogetherView.as_view()),
    path('train/', TrainModelView.as_view()),
    path('interaction/', RecordInteractionView.as_view()),

    # Hybrid Recommendations (LSTM + Graph + RAG)
    path('hybrid/', HybridRecommendationsView.as_view()),
    path('hybrid/chatbot/', HybridChatbotView.as_view()),

    # LSTM Model
    path('lstm/predict/', LSTMPredictionsView.as_view()),
    path('lstm/train/', LSTMTrainView.as_view()),

    # Knowledge Graph (Neo4j)
    path('graph/recommend/', GraphRecommendationsView.as_view()),
    path('graph/similar/<uuid:product_id>/', GraphSimilarView.as_view()),
    path('graph/sync/', GraphSyncView.as_view()),
    path('graph/stats/', GraphStatsView.as_view()),

    # RAG (Vector Search + LLM)
    path('rag/search/', RAGSearchView.as_view()),
    path('rag/index/', RAGIndexView.as_view()),

    # Train All Models
    path('train-all/', TrainAllModelsView.as_view()),

    # Seed Data (for testing)
    path('seed/', SeedDataView.as_view()),

    # Behavior Tracking API
    path('track/', TrackBehaviorView.as_view()),
    path('behaviors/stats/', BehaviorStatsView.as_view()),
]
