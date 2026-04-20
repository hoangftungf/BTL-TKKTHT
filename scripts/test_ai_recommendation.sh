#!/bin/bash

# ============================================
# Test AI Recommendation Service
# ============================================

BASE_URL="${AI_RECOMMENDATION_URL:-http://localhost:8010}"

echo "=== AI Recommendation Service Test ==="
echo "Base URL: $BASE_URL"
echo ""

# 1. Health Check
echo "1. Health Check..."
curl -s "$BASE_URL/health/" | jq .
echo ""

# 2. Seed Sample Data
echo "2. Seeding sample data (10 users)..."
curl -s -X POST "$BASE_URL/seed/" \
  -H "Content-Type: application/json" \
  -d '{"clear": true}' | jq .
echo ""

# 3. Train Collaborative Filtering Model
echo "3. Training Collaborative Filtering model..."
curl -s -X POST "$BASE_URL/train/" | jq .
echo ""

# 4. Train LSTM Model
echo "4. Training LSTM model..."
curl -s -X POST "$BASE_URL/lstm/train/" \
  -H "Content-Type: application/json" \
  -d '{"epochs": 20, "batch_size": 32}' | jq .
echo ""

# 5. Index products for RAG
echo "5. Indexing products for RAG..."
curl -s -X POST "$BASE_URL/rag/index/" | jq .
echo ""

# 6. Sync Knowledge Graph
echo "6. Syncing Knowledge Graph..."
curl -s -X POST "$BASE_URL/graph/sync/" | jq .
echo ""

# 7. Get Graph Stats
echo "7. Knowledge Graph Stats..."
curl -s "$BASE_URL/graph/stats/" | jq .
echo ""

# 8. Test Trending Products
echo "8. Trending Products..."
curl -s "$BASE_URL/trending/?limit=5" | jq .
echo ""

# 9. Test Similar Products (iPhone)
echo "9. Similar Products for iPhone 15 Pro Max..."
curl -s "$BASE_URL/product/e1111111-1111-1111-1111-111111111111/?limit=5" | jq .
echo ""

# 10. Test Hybrid Recommendations for User A (tech_lover)
echo "10. Hybrid Recommendations for User A (tech_lover)..."
curl -s "$BASE_URL/hybrid/?user_id=11111111-1111-1111-1111-111111111111&limit=5" | jq .
echo ""

# 11. Test Hybrid Recommendations with Query
echo "11. Hybrid Recommendations with query 'laptop gaming'..."
curl -s "$BASE_URL/hybrid/?query=laptop%20gaming&limit=5" | jq .
echo ""

# 12. Test RAG Search
echo "12. RAG Semantic Search for 'tai nghe chống ồn'..."
curl -s "$BASE_URL/rag/search/?query=tai%20nghe%20ch%E1%BB%91ng%20%E1%BB%93n&limit=5" | jq .
echo ""

# 13. Test Hybrid Chatbot
echo "13. Chatbot Query: 'Tôi cần mua điện thoại giá tốt'..."
curl -s -X POST "$BASE_URL/hybrid/chatbot/" \
  -H "Content-Type: application/json" \
  -d '{"query": "Tôi cần mua điện thoại giá tốt", "user_id": "11111111-1111-1111-1111-111111111111"}' | jq .
echo ""

# 14. Test Frequently Bought Together
echo "14. Frequently Bought Together with PlayStation 5..."
curl -s "$BASE_URL/frequently-bought/g1111111-1111-1111-1111-111111111111/?limit=5" | jq .
echo ""

echo "=== Test Complete ==="
