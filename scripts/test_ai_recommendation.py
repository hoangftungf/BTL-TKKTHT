"""
Test script for AI Recommendation Service
Usage: python test_ai_recommendation.py [base_url]
"""

import sys
import json
import time
import httpx

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8010"

def print_response(title, response):
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except:
        print(response.text[:500])
    print()

def main():
    client = httpx.Client(timeout=60.0)

    print(f"\nTesting AI Recommendation Service at: {BASE_URL}\n")

    # 1. Health Check
    r = client.get(f"{BASE_URL}/health/")
    print_response("1. Health Check", r)

    # 2. Seed Sample Data
    r = client.post(f"{BASE_URL}/seed/", json={"clear": True})
    print_response("2. Seed Sample Data (10 users)", r)

    if r.status_code != 200:
        print("Failed to seed data. Exiting.")
        return

    users = r.json().get('users', [])
    print("Sample Users:")
    for u in users:
        print(f"  - {u['name']} ({u['type']}): {u['id']}")

    # 3. Train Collaborative Filtering
    print("\n3. Training Collaborative Filtering model...")
    r = client.post(f"{BASE_URL}/train/")
    print_response("Collaborative Filtering Training", r)

    # 4. Train LSTM (with fewer epochs for testing)
    print("\n4. Training LSTM model (20 epochs)...")
    r = client.post(f"{BASE_URL}/lstm/train/", json={"epochs": 20, "batch_size": 32})
    print_response("LSTM Training", r)

    # 5. Index products for RAG
    print("\n5. Indexing products for RAG...")
    r = client.post(f"{BASE_URL}/rag/index/")
    print_response("RAG Indexing", r)

    # 6. Sync Knowledge Graph
    print("\n6. Syncing Knowledge Graph...")
    r = client.post(f"{BASE_URL}/graph/sync/")
    print_response("Graph Sync", r)

    # 7. Graph Stats
    r = client.get(f"{BASE_URL}/graph/stats/")
    print_response("7. Knowledge Graph Stats", r)

    # 8. Trending Products
    r = client.get(f"{BASE_URL}/trending/", params={"limit": 5})
    print_response("8. Trending Products", r)

    # 9. Similar Products (iPhone)
    r = client.get(f"{BASE_URL}/product/e1111111-1111-1111-1111-111111111111/", params={"limit": 5})
    print_response("9. Similar Products (iPhone 15 Pro Max)", r)

    # 10. Hybrid Recommendations for tech_lover user
    r = client.get(f"{BASE_URL}/hybrid/", params={
        "user_id": "11111111-1111-1111-1111-111111111111",
        "limit": 5
    })
    print_response("10. Hybrid Recommendations (User A - tech_lover)", r)

    # 11. Hybrid Recommendations for fashionista user
    r = client.get(f"{BASE_URL}/hybrid/", params={
        "user_id": "22222222-2222-2222-2222-222222222222",
        "limit": 5
    })
    print_response("11. Hybrid Recommendations (User B - fashionista)", r)

    # 12. Hybrid with query
    r = client.get(f"{BASE_URL}/hybrid/", params={
        "query": "laptop gaming cao cap",
        "limit": 5
    })
    print_response("12. Hybrid with Query 'laptop gaming cao cap'", r)

    # 13. RAG Search
    r = client.get(f"{BASE_URL}/rag/search/", params={
        "query": "tai nghe chong on",
        "limit": 5
    })
    print_response("13. RAG Search 'tai nghe chong on'", r)

    # 14. RAG with response generation
    r = client.post(f"{BASE_URL}/rag/search/", json={
        "query": "Toi can mua dien thoai chup hinh dep",
        "limit": 5
    })
    print_response("14. RAG Search with Response Generation", r)

    # 15. Chatbot
    r = client.post(f"{BASE_URL}/hybrid/chatbot/", json={
        "query": "Toi muon mua may choi game, co gi phu hop khong?",
        "user_id": "33333333-3333-3333-3333-333333333333"  # gamer user
    })
    print_response("15. Hybrid Chatbot (gamer user)", r)

    # 16. Frequently Bought Together
    r = client.get(f"{BASE_URL}/frequently-bought/g1111111-1111-1111-1111-111111111111/", params={"limit": 5})
    print_response("16. Frequently Bought Together (PlayStation 5)", r)

    # 17. Graph Similar Products
    r = client.get(f"{BASE_URL}/graph/similar/e3333333-3333-3333-3333-333333333333/", params={"limit": 5})
    print_response("17. Graph Similar Products (MacBook Pro)", r)

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

    client.close()

if __name__ == "__main__":
    main()
