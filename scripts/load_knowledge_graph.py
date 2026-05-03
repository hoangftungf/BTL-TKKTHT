"""
Bước 2b: Load dữ liệu vào Neo4j Knowledge Graph
Tạo graph từ data_user500.csv và products.csv
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Neo4j driver
try:
    from neo4j import GraphDatabase
except ImportError:
    print("Installing neo4j driver...")
    os.system("pip install neo4j --quiet")
    from neo4j import GraphDatabase

# Configuration
NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'password123')


class KnowledgeGraphLoader:
    """
    Load data vào Neo4j Knowledge Graph

    Graph Schema:
    - (:User {id, name})
    - (:Product {id, name, category, brand, price})
    - (:Category {name})
    - (:Brand {name})
    - (:Action {name})

    Relationships:
    - (User)-[:VIEWED {count, last_time}]->(Product)
    - (User)-[:CLICKED {count, last_time}]->(Product)
    - (User)-[:ADDED_TO_CART {count, last_time}]->(Product)
    - (User)-[:PURCHASED {count, last_time}]->(Product)
    - (User)-[:WISHLISTED]->(Product)
    - (User)-[:SEARCHED]->(Product)
    - (User)-[:REVIEWED]->(Product)
    - (User)-[:SHARED]->(Product)
    - (Product)-[:BELONGS_TO]->(Category)
    - (Product)-[:MADE_BY]->(Brand)
    - (User)-[:SIMILAR_TO {score}]->(User)
    - (Product)-[:SIMILAR_TO {score}]->(Product)
    """

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print(f"Connected to Neo4j at {uri}")

    def close(self):
        self.driver.close()

    def clear_database(self):
        """Xóa toàn bộ dữ liệu trong graph"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("Database cleared")

    def create_indexes(self):
        """Tạo indexes cho performance"""
        with self.driver.session() as session:
            # User index
            session.run("CREATE INDEX user_id IF NOT EXISTS FOR (u:User) ON (u.id)")
            # Product index
            session.run("CREATE INDEX product_id IF NOT EXISTS FOR (p:Product) ON (p.id)")
            # Category index
            session.run("CREATE INDEX category_name IF NOT EXISTS FOR (c:Category) ON (c.name)")
            # Brand index
            session.run("CREATE INDEX brand_name IF NOT EXISTS FOR (b:Brand) ON (b.name)")
        print("Indexes created")

    def load_products(self, products_df):
        """Load products vào graph"""
        print(f"\nLoading {len(products_df)} products...")

        with self.driver.session() as session:
            for _, row in products_df.iterrows():
                # Create Product node
                session.run("""
                    MERGE (p:Product {id: $id})
                    SET p.name = $name, p.price = $price
                """, id=row['product_id'], name=row['name'], price=row['price'])

                # Create Category and relationship
                session.run("""
                    MERGE (c:Category {name: $category})
                    WITH c
                    MATCH (p:Product {id: $product_id})
                    MERGE (p)-[:BELONGS_TO]->(c)
                """, category=row['category'], product_id=row['product_id'])

                # Create Brand and relationship
                session.run("""
                    MERGE (b:Brand {name: $brand})
                    WITH b
                    MATCH (p:Product {id: $product_id})
                    MERGE (p)-[:MADE_BY]->(b)
                """, brand=row['brand'], product_id=row['product_id'])

        print(f"  Loaded {len(products_df)} products")
        print(f"  Categories: {products_df['category'].nunique()}")
        print(f"  Brands: {products_df['brand'].nunique()}")

    def load_users(self, behavior_df):
        """Load users vào graph"""
        users = behavior_df['user_id'].unique()
        print(f"\nLoading {len(users)} users...")

        with self.driver.session() as session:
            for user_id in users:
                session.run("""
                    MERGE (u:User {id: $id})
                    SET u.name = $name
                """, id=user_id, name=f"User {user_id}")

        print(f"  Loaded {len(users)} users")

    def load_interactions(self, behavior_df):
        """Load interactions (relationships) vào graph"""
        print(f"\nLoading {len(behavior_df)} interactions...")

        # Mapping action to relationship type
        action_to_rel = {
            'view': 'VIEWED',
            'click': 'CLICKED',
            'add_to_cart': 'ADDED_TO_CART',
            'purchase': 'PURCHASED',
            'wishlist': 'WISHLISTED',
            'search': 'SEARCHED',
            'review': 'REVIEWED',
            'share': 'SHARED'
        }

        # Aggregate interactions
        agg_df = behavior_df.groupby(['user_id', 'product_id', 'action']).agg({
            'timestamp': ['count', 'max'],
            'duration': 'sum'
        }).reset_index()
        agg_df.columns = ['user_id', 'product_id', 'action', 'count', 'last_time', 'total_duration']

        print(f"  Aggregated to {len(agg_df)} unique interactions")

        with self.driver.session() as session:
            for _, row in agg_df.iterrows():
                rel_type = action_to_rel.get(row['action'], 'INTERACTED')

                # Create relationship with properties
                query = f"""
                    MATCH (u:User {{id: $user_id}})
                    MATCH (p:Product {{id: $product_id}})
                    MERGE (u)-[r:{rel_type}]->(p)
                    SET r.count = $count,
                        r.last_time = $last_time,
                        r.total_duration = $total_duration
                """
                session.run(query,
                    user_id=row['user_id'],
                    product_id=row['product_id'],
                    count=int(row['count']),
                    last_time=row['last_time'],
                    total_duration=int(row['total_duration'])
                )

        # Print statistics per action
        print("\n  Interactions by type:")
        for action, count in behavior_df['action'].value_counts().items():
            print(f"    {action}: {count:,}")

    def compute_user_similarity(self, top_n=5):
        """Tính user similarity dựa trên sản phẩm đã tương tác"""
        print("\nComputing user similarities...")

        with self.driver.session() as session:
            # Users who interacted with same products
            result = session.run("""
                MATCH (u1:User)-[:PURCHASED|VIEWED|CLICKED]->(p:Product)<-[:PURCHASED|VIEWED|CLICKED]-(u2:User)
                WHERE u1.id < u2.id
                WITH u1, u2, COUNT(DISTINCT p) AS common_products
                WHERE common_products >= 3
                MERGE (u1)-[r:SIMILAR_TO]->(u2)
                SET r.score = common_products
                RETURN COUNT(*) AS pairs_created
            """)
            pairs = result.single()['pairs_created']
            print(f"  Created {pairs} user similarity relationships")

    def compute_product_similarity(self):
        """Tính product similarity dựa trên co-purchase"""
        print("\nComputing product similarities...")

        with self.driver.session() as session:
            # Products bought together
            result = session.run("""
                MATCH (p1:Product)<-[:PURCHASED]-(u:User)-[:PURCHASED]->(p2:Product)
                WHERE p1.id < p2.id
                WITH p1, p2, COUNT(DISTINCT u) AS co_purchases
                WHERE co_purchases >= 2
                MERGE (p1)-[r:SIMILAR_TO]->(p2)
                SET r.score = co_purchases
                RETURN COUNT(*) AS pairs_created
            """)
            pairs = result.single()['pairs_created']
            print(f"  Created {pairs} product similarity relationships")

    def get_stats(self):
        """Lấy thống kê graph"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User) WITH COUNT(u) AS users
                MATCH (p:Product) WITH users, COUNT(p) AS products
                MATCH (c:Category) WITH users, products, COUNT(c) AS categories
                MATCH (b:Brand) WITH users, products, categories, COUNT(b) AS brands
                MATCH ()-[r]->() WITH users, products, categories, brands, COUNT(r) AS relationships
                RETURN users, products, categories, brands, relationships
            """)
            return result.single()

    def get_sample_queries(self):
        """Chạy một số queries mẫu"""
        print("\n" + "="*60)
        print("SAMPLE QUERIES")
        print("="*60)

        with self.driver.session() as session:
            # 1. Top users by interactions
            print("\n1. Top 5 users by total interactions:")
            result = session.run("""
                MATCH (u:User)-[r]->(p:Product)
                RETURN u.id AS user, COUNT(r) AS interactions
                ORDER BY interactions DESC
                LIMIT 5
            """)
            for record in result:
                print(f"   {record['user']}: {record['interactions']} interactions")

            # 2. Top products by purchases
            print("\n2. Top 5 products by purchases:")
            result = session.run("""
                MATCH (u:User)-[r:PURCHASED]->(p:Product)
                RETURN p.id AS product, p.name AS name, COUNT(r) AS purchases
                ORDER BY purchases DESC
                LIMIT 5
            """)
            for record in result:
                print(f"   {record['product']}: {record['purchases']} purchases")

            # 3. Category popularity
            print("\n3. Category popularity (by interactions):")
            result = session.run("""
                MATCH (u:User)-[r]->(p:Product)-[:BELONGS_TO]->(c:Category)
                RETURN c.name AS category, COUNT(r) AS interactions
                ORDER BY interactions DESC
            """)
            for record in result:
                print(f"   {record['category']}: {record['interactions']} interactions")

            # 4. User recommendations (collaborative filtering)
            print("\n4. Sample recommendation for U0001:")
            result = session.run("""
                MATCH (u:User {id: 'U0001'})-[:PURCHASED]->(p:Product)<-[:PURCHASED]-(other:User)
                MATCH (other)-[:PURCHASED]->(rec:Product)
                WHERE NOT (u)-[:PURCHASED]->(rec)
                RETURN rec.id AS product, rec.name AS name, COUNT(DISTINCT other) AS score
                ORDER BY score DESC
                LIMIT 5
            """)
            for record in result:
                print(f"   {record['product']}: score={record['score']}")

            # 5. Products frequently bought together
            print("\n5. Products frequently bought together with P0001:")
            result = session.run("""
                MATCH (p:Product {id: 'P0001'})<-[:PURCHASED]-(u:User)-[:PURCHASED]->(other:Product)
                WHERE other.id <> 'P0001'
                RETURN other.id AS product, other.name AS name, COUNT(DISTINCT u) AS co_purchases
                ORDER BY co_purchases DESC
                LIMIT 5
            """)
            for record in result:
                print(f"   {record['product']}: {record['co_purchases']} co-purchases")


def main():
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    products_path = os.path.join(base_dir, 'data', 'products.csv')
    behavior_path = os.path.join(base_dir, 'data', 'data_user500.csv')

    print("="*60)
    print("BUOC 2b: LOAD DATA VAO NEO4J KNOWLEDGE GRAPH")
    print("="*60)

    # Load CSV files
    print(f"\nLoading data files...")
    products_df = pd.read_csv(products_path)
    behavior_df = pd.read_csv(behavior_path)

    print(f"  Products: {len(products_df)}")
    print(f"  Behaviors: {len(behavior_df)}")

    # Connect to Neo4j
    try:
        loader = KnowledgeGraphLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    except Exception as e:
        print(f"\nError: Cannot connect to Neo4j at {NEO4J_URI}")
        print(f"Make sure Neo4j is running: docker-compose up neo4j -d")
        print(f"Error details: {e}")

        # Print Cypher queries for manual execution
        print("\n" + "="*60)
        print("CYPHER QUERIES (run manually in Neo4j Browser)")
        print("="*60)
        print("""
// 1. Create indexes
CREATE INDEX user_id IF NOT EXISTS FOR (u:User) ON (u.id);
CREATE INDEX product_id IF NOT EXISTS FOR (p:Product) ON (p.id);
CREATE INDEX category_name IF NOT EXISTS FOR (c:Category) ON (c.name);
CREATE INDEX brand_name IF NOT EXISTS FOR (b:Brand) ON (b.name);

// 2. Sample: Create a product
MERGE (p:Product {id: 'P0001'})
SET p.name = 'Apple Laptop Model 1', p.price = 49864611;

MERGE (c:Category {name: 'Laptop'})
WITH c
MATCH (p:Product {id: 'P0001'})
MERGE (p)-[:BELONGS_TO]->(c);

// 3. Sample: Create user and interaction
MERGE (u:User {id: 'U0001'})
SET u.name = 'User U0001';

MATCH (u:User {id: 'U0001'})
MATCH (p:Product {id: 'P0001'})
MERGE (u)-[r:VIEWED]->(p)
SET r.count = 5, r.last_time = '2026-04-01';

// 4. Query: Get recommendations
MATCH (u:User {id: 'U0001'})-[:PURCHASED]->(p:Product)<-[:PURCHASED]-(other:User)
MATCH (other)-[:PURCHASED]->(rec:Product)
WHERE NOT (u)-[:PURCHASED]->(rec)
RETURN rec.id, rec.name, COUNT(DISTINCT other) AS score
ORDER BY score DESC
LIMIT 10;
        """)
        return

    try:
        # Clear and setup
        loader.clear_database()
        loader.create_indexes()

        # Load data
        loader.load_products(products_df)
        loader.load_users(behavior_df)
        loader.load_interactions(behavior_df)

        # Compute similarities
        loader.compute_user_similarity()
        loader.compute_product_similarity()

        # Get statistics
        print("\n" + "="*60)
        print("KNOWLEDGE GRAPH STATISTICS")
        print("="*60)
        stats = loader.get_stats()
        print(f"""
  Nodes:
    - Users: {stats['users']}
    - Products: {stats['products']}
    - Categories: {stats['categories']}
    - Brands: {stats['brands']}

  Total Relationships: {stats['relationships']}
        """)

        # Sample queries
        loader.get_sample_queries()

        print("\n" + "="*60)
        print("HOAN THANH BUOC 2b!")
        print("="*60)
        print(f"""
Neo4j Browser: http://localhost:7474
Username: {NEO4J_USER}
Password: {NEO4J_PASSWORD}

Graph da san sang de su dung voi RAG!
        """)

    finally:
        loader.close()


if __name__ == '__main__':
    main()
