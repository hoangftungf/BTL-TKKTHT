# AI User Behavior Pipeline

Complete pipeline for generating user behavior data and loading into Neo4j for AI recommendations.

## Overview

This pipeline creates:
- **500 users** with consistent UUIDs
- **10,000-20,000 behaviors** (20-50 per user)
- **Neo4j graph** with users, products, categories
- **Intelligent relationships**: SIMILAR_TO, INTEREST, BOUGHT_TOGETHER

## Quick Start

### Using Docker (Recommended)

```bash
# Start services
docker-compose up -d postgres neo4j ai-recommendation

# Run migrations
docker-compose exec ai-recommendation python manage.py migrate

# Run full pipeline
docker-compose exec ai-recommendation python manage.py run_full_pipeline --clear
```

### Step-by-Step Execution

```bash
# Step 1: Seed 500 users
docker-compose exec ai-recommendation python manage.py seed_users --count 500

# Step 2: Seed behaviors (10,000-20,000)
docker-compose exec ai-recommendation python manage.py seed_behaviors --clear

# Step 3: Push to Neo4j
docker-compose exec ai-recommendation python manage.py push_to_neo4j --clear

# Step 4: Enhance graph
docker-compose exec ai-recommendation python manage.py enhance_graph

# Step 5: Validate
docker-compose exec ai-recommendation python manage.py validate_pipeline
```

## Data Distribution

### Action Types
- **view**: 60% - User views a product
- **cart**: 20% - User adds to cart
- **purchase**: 10% - User purchases
- **search**: 10% - User searches (may or may not lead to product)

### Behavior Logic (Realistic Funnel)
1. **View** - Random product (biased to preferred categories)
2. **Cart** - From previously viewed products
3. **Purchase** - From cart (or direct from viewed)
4. **Search** - Random search query, may link to product

## Neo4j Schema

### Nodes
- `(:User {id, name})`
- `(:Product {id, name, price, popularity})`
- `(:Category {name})`

### Relationships
- `(User)-[:VIEW {count}]->(Product)`
- `(User)-[:CART {count}]->(Product)`
- `(User)-[:PURCHASE {count}]->(Product)`
- `(User)-[:SEARCH {query}]->(Product)`
- `(Product)-[:BELONGS_TO]->(Category)`
- `(Product)-[:SIMILAR_TO {co_views, score}]->(Product)`
- `(User)-[:INTEREST {score}]->(Category)`
- `(Product)-[:BOUGHT_TOGETHER {count}]->(Product)`

## Test Queries

### View User-Product Relationships
```cypher
MATCH (u:User)-[:VIEW]->(p:Product)
RETURN u, p LIMIT 20
```

### View Similar Products
```cypher
MATCH (p1:Product)-[:SIMILAR_TO]->(p2:Product)
RETURN p1.name, p2.name, r.co_views
ORDER BY r.co_views DESC
LIMIT 20
```

### View User Interests
```cypher
MATCH (u:User)-[r:INTEREST]->(c:Category)
RETURN u.name, c.name, r.score
ORDER BY r.score DESC
LIMIT 20
```

### Get Popular Products
```cypher
MATCH (p:Product)
WHERE p.popularity > 0
RETURN p.name, p.popularity
ORDER BY p.popularity DESC
LIMIT 20
```

### Get Recommendations for User
```cypher
MATCH (u:User {id: $user_id})-[:INTEREST]->(c:Category)<-[:BELONGS_TO]-(p:Product)
WHERE NOT (u)-[:PURCHASE]->(p)
RETURN p.name, p.popularity
ORDER BY p.popularity DESC
LIMIT 10
```

## Files Created

### Management Commands (services/ai-recommendation)
- `seed_users.py` - Create 500 users
- `seed_behaviors.py` - Create 10,000-20,000 behaviors
- `push_to_neo4j.py` - Push data to Neo4j
- `enhance_graph.py` - Create intelligent relationships
- `validate_pipeline.py` - Validate data
- `run_full_pipeline.py` - Run all steps

### Services
- `services/neo4j_client.py` - Reusable Neo4j client

### Standalone Scripts
- `scripts/seed_users.py`
- `scripts/seed_behaviors.py`
- `scripts/push_to_neo4j.py`
- `scripts/enhance_graph.py`
- `scripts/run_ai_pipeline.py`

## Model: UserBehavior

```python
class UserBehavior(models.Model):
    ACTION_CHOICES = [
        ('view', 'Xem sản phẩm'),
        ('cart', 'Thêm giỏ hàng'),
        ('purchase', 'Mua hàng'),
        ('search', 'Tìm kiếm'),
    ]

    id = models.UUIDField(primary_key=True)
    user_id = models.UUIDField(db_index=True)
    product_id = models.UUIDField(null=True, db_index=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    search_query = models.CharField(max_length=500, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

## Expected Results

After running the full pipeline:
- **500 users** in database
- **~15,000 behaviors** (average 30 per user)
- **500 User nodes** in Neo4j
- **200+ Product nodes** in Neo4j
- **5,000+ relationships** in Neo4j
- **SIMILAR_TO relationships** between co-viewed products
- **INTEREST relationships** between users and categories
- **Popularity scores** on products

## Integration

This data is ready for:
1. **Recommendation System** - Use Neo4j graph queries
2. **RAG Chatbot** - Query knowledge graph for context
3. **AI Model Training** - Export behaviors for ML
4. **Analytics** - Analyze user behavior patterns
