import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_service.settings')
django.setup()

import httpx
from chatbot_app.tasks import update_product_knowledge_base_async
from neo4j import GraphDatabase

# 1. Clean Neo4j variant nodes and relationships to prevent duplicates
driver = GraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', 'password123'))
with driver.session() as session:
    session.run("MATCH (v:Variant) DETACH DELETE v")
    session.run("MATCH (co:Color) DETACH DELETE co")
    session.run("MATCH (sz:Size) DETACH DELETE sz")
driver.close()
print("Cleaned Neo4j variants, colors, and sizes.")

# 2. Sync the three products sequentially
product_ids = [
    '8cff55ec-12f4-48fa-ac4e-21b6efbced3a',  # Xiaomi
    'c708be8d-0b05-405f-8f6f-992860fd3ad2',  # Dell
    '9683a141-51bd-47f9-a468-88f9acceb9b5'   # Nike
]

for pid in product_ids:
    url = f"http://product-service:8003/{pid}/"
    r = httpx.get(url)
    if r.status_code == 200:
        product_data = r.json()
        print(f"Syncing product {product_data.get('name')} ({pid})...")
        update_product_knowledge_base_async(product_data)
    else:
        print(f"Failed to fetch product {pid}: {r.status_code}")

print("Sync completed successfully!")
