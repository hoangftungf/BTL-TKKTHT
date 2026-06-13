import os
import json
import logging
from celery import shared_task
from django.conf import settings
from neo4j import GraphDatabase
import numpy as np

logger = logging.getLogger(__name__)

# Load configurations
NEO4J_URI = getattr(settings, 'NEO4J_URI', 'bolt://neo4j:7687')
NEO4J_USER = getattr(settings, 'NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = getattr(settings, 'NEO4J_PASSWORD', 'password123')
AI_INDEX_DIR = getattr(settings, 'AI_INDEX_DIR', '/app/ai_index')

def extract_color_material(name, description):
    name_lower = name.lower() if name else ""
    desc_lower = description.lower() if description else ""
    
    colors = {
        'Đen': ['mau den', 'màu đen', 'đen', 'black'],
        'Trắng': ['mau trang', 'màu trắng', 'trắng', 'white'],
        'Hồng': ['mau hong', 'màu hồng', 'hồng', 'pink'],
        'Đỏ': ['mau do', 'màu đỏ', 'đỏ', 'red'],
        'Xanh': ['mau xanh', 'màu xanh', 'xanh', 'blue', 'green'],
        'Vàng': ['mau vang', 'màu vàng', 'vàng', 'yellow'],
        'Nâu': ['mau nau', 'màu nâu', 'nâu', 'brown'],
        'Xám': ['mau xam', 'màu xám', 'xám', 'grey', 'gray'],
        'Cam': ['mau cam', 'màu cam', 'cam', 'orange'],
        'Tím': ['mau tim', 'màu tím', 'tím', 'purple']
    }
    
    materials = {
        'Jean': ['jean', 'bò', 'denim'],
        'Cotton': ['cotton', 'thun'],
        'Lụa': ['lụa', 'silk'],
        'Da': [' da ', 'da bò', 'da cá', 'leather'],
        'Len': ['len', 'wool'],
        'Polyester': ['polyester', 'poly', 'nỉ', 'spandex'],
        'Kaki': ['kaki', 'khaki'],
        'Linen': ['linen', 'đũi']
    }
    
    color = next((c for c, kws in colors.items() if any(kw in name_lower or kw in desc_lower for kw in kws)), None)
    material = next((m for m, kws in materials.items() if any(kw in name_lower or kw in desc_lower for kw in kws)), None)
    return color, material

@shared_task
def update_product_knowledge_base_async(product_data):
    """
    Celery task to update Neo4j graph and local FAISS vector store.
    """
    pid = product_data.get('id')
    name = product_data.get('name', '')
    price = product_data.get('price', 0)
    brand = product_data.get('brand', '')
    category = product_data.get('category', '')
    if isinstance(category, dict):
        category = category.get('name', '')
    description = product_data.get('description', '')
    status = product_data.get('status', 'active')
    stock_quantity = product_data.get('stock_quantity', 0)
    image_url = product_data.get('image_url', '')
    if not image_url:
        primary_img = product_data.get('primary_image')
        if isinstance(primary_img, dict):
            image_url = primary_img.get('image', '')
        elif product_data.get('images'):
            images = product_data.get('images', [])
            if images and isinstance(images[0], dict):
                image_url = images[0].get('image', '')
            elif images and isinstance(images[0], str):
                image_url = images[0]

    logger.info(f"[Celery] Asynchronously updating product {pid} in KB...")

    # 1. Update Neo4j Graph
    color, material = extract_color_material(name, description)
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session() as session:
            # Update product node basic attributes, status, stock, and specifications
            import json
            specs = product_data.get('specifications', {})
            specs_json = json.dumps(specs, ensure_ascii=False)

            session.run("""
                MERGE (p:Product {id: $id})
                SET p.name = $name, 
                    p.price = $price, 
                    p.brand = $brand, 
                    p.status = $status, 
                    p.stock_quantity = $stock_quantity,
                    p.specifications = $specifications,
                    p.image_url = $image_url
            """, id=str(pid), name=name, price=float(price), brand=brand or "", status=status, stock_quantity=int(stock_quantity), specifications=specs_json, image_url=image_url)

            # Update Category relation
            if category:
                session.run("""
                    MERGE (c:Category {name: $category})
                    WITH c
                    MATCH (p:Product {id: $product_id})
                    MERGE (p)-[:BELONGS_TO]->(c)
                """, category=category, product_id=str(pid))

            # Update Brand relation
            if brand:
                session.run("""
                    MERGE (b:Brand {name: $brand})
                    WITH b
                    MATCH (p:Product {id: $product_id})
                    MERGE (p)-[:MADE_BY]->(b)
                """, brand=brand, product_id=str(pid))

            # Update Color relation
            if color:
                session.run("""
                    MERGE (co:Color {name: $color})
                    WITH co
                    MATCH (p:Product {id: $product_id})
                    MERGE (p)-[:HAS_COLOR]->(co)
                """, color=color, product_id=str(pid))

            # Update Material relation
            if material:
                session.run("""
                    MERGE (ma:Material {name: $material})
                    WITH ma
                    MATCH (p:Product {id: $product_id})
                    MERGE (p)-[:HAS_MATERIAL]->(ma)
                """, material=material, product_id=str(pid))

            # Delete existing variants of this product to keep graph clean
            session.run("""
                MATCH (p:Product {id: $product_id})-[r:HAS_VARIANT]->(v:Variant)
                DETACH DELETE v
            """, product_id=str(pid))

            # Add new variants
            variants = product_data.get('variants', [])
            for v in variants:
                v_id = v.get('id')
                v_name = v.get('name', '')
                v_price = v.get('price', 0)
                v_sku = v.get('sku', '')
                v_stock = v.get('stock_quantity', 0)
                v_attrs = v.get('attributes', {})

                # Merge Variant node and link to Product
                import json
                v_attrs_json = json.dumps(v_attrs, ensure_ascii=False)
                session.run("""
                    MATCH (p:Product {id: $product_id})
                    MERGE (v:Variant {id: $variant_id})
                    SET v.name = $name,
                        v.price = $price,
                        v.sku = $sku,
                        v.stock_quantity = $stock_quantity,
                        v.attributes = $attributes
                    MERGE (p)-[:HAS_VARIANT]->(v)
                """, product_id=str(pid), variant_id=str(v_id), name=v_name, price=float(v_price), sku=v_sku, stock_quantity=int(v_stock), attributes=v_attrs_json)

                # If variant has color attribute, create/link Color node
                v_color = v_attrs.get('color') or v_attrs.get('Màu sắc') or v_attrs.get('Màu')
                if v_color:
                    session.run("""
                        MATCH (v:Variant {id: $variant_id})
                        MERGE (co:Color {name: $color})
                        MERGE (v)-[:HAS_COLOR]->(co)
                    """, variant_id=str(v_id), color=str(v_color))

                # If variant has size attribute, create/link Size node
                v_size = v_attrs.get('size') or v_attrs.get('Kích thước') or v_attrs.get('Size') or v_attrs.get('Kích cỡ')
                if v_size:
                    session.run("""
                        MATCH (v:Variant {id: $variant_id})
                        MERGE (sz:Size {name: $size})
                        MERGE (v)-[:HAS_SIZE]->(sz)
                    """, variant_id=str(v_id), size=str(v_size))

        driver.close()
        logger.info(f"[Celery] Successfully updated product {pid} in Neo4j.")
    except Exception as exc:
        logger.error(f"[Celery] Error updating product {pid} in Neo4j: {exc}")

    # 2. Update FAISS Vector Store
    try:
        from chatbot_app.engine import ProductVectorStore, TextEmbedder, RAGPipeline
        
        # Initialize Vector Store and load existing index
        store = ProductVectorStore()
        store.load_local(AI_INDEX_DIR)
        
        # Build text representation & generate embedding
        text_rep = RAGPipeline._build_product_text({
            'name': name,
            'brand': brand,
            'category': category,
            'description': description,
            'color': color,
            'material': material,
            'specifications': product_data.get('specifications', {}),
            'variants': product_data.get('variants', [])
        })
        
        ollama_host = getattr(settings, 'OLLAMA_HOST', 'http://ollama:11434')
        embedder = TextEmbedder(ollama_host)
        embeddings = embedder.embed([text_rep])
        
        if len(embeddings) > 0:
            # Check if product already exists in vector store
            pid_str = str(pid)
            if pid_str in store.product_ids:
                idx = store.product_ids.index(pid_str)
                # Remove from FAISS index and lists
                # Note: FAISS doesn't easily support single item deletion without rebuilding,
                # but we can update self.product_data and rebuild the index in memory.
                # Since the store is small (500 products), we can rebuild it easily.
                store.product_data[pid_str] = {
                    'name': name,
                    'price': float(price),
                    'category': category,
                    'brand': brand or "",
                    'description': description[:300],
                    'image_url': image_url,
                    'status': status,
                    'stock_quantity': int(stock_quantity),
                    'color': color,
                    'material': material
                }
                
                # Rebuild embeddings list and index
                all_pids = list(store.product_data.keys())
                all_texts = []
                for p_id in all_pids:
                    p_data = store.product_data[p_id]
                    all_texts.append(RAGPipeline._build_product_text(p_data))
                
                all_embs = embedder.embed(all_texts)
                
                # Clear and re-populate store
                store.product_ids = []
                store.index = None
                store._embeddings = []
                for p_id, emb in zip(all_pids, all_embs):
                    p_data = store.product_data[p_id]
                    store.add(p_id, emb, p_data)
            else:
                # Add new product
                store.add(
                    product_id=pid_str,
                    embedding=embeddings[0],
                    product_data={
                        'name': name,
                        'price': float(price),
                        'category': category,
                        'brand': brand or "",
                        'description': description[:300],
                        'image_url': image_url,
                        'status': status,
                        'stock_quantity': int(stock_quantity),
                        'color': color,
                        'material': material
                    }
                )
            
            # Save local
            store.save_local(AI_INDEX_DIR)
            logger.info(f"[Celery] Successfully updated product {pid} in FAISS store.")
    except Exception as exc:
        logger.error(f"[Celery] Error updating product {pid} in FAISS: {exc}")
