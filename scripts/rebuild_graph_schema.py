#!/usr/bin/env python
"""
Giai đoạn 2.1: Rebuild Graph Schema
===================================
Standalone script to restructure Neo4j schema by extracting Brand, Material,
and Color properties from existing Product nodes and creating independent nodes.

Usage:
    python scripts/rebuild_graph_schema.py
"""

import os
import re
from neo4j import GraphDatabase

NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'password123')

COLORS = {
    'Đen': ['mau den', 'màu đen', 'đen', 'black', 'den'],
    'Trắng': ['mau trang', 'màu trắng', 'trắng', 'white', 'trang'],
    'Hồng': ['mau hong', 'màu hồng', 'hồng', 'pink', 'hong'],
    'Đỏ': ['mau do', 'màu đỏ', 'đỏ', 'red', 'do'],
    'Xanh': ['mau xanh', 'màu xanh', 'xanh', 'blue', 'green'],
    'Vàng': ['mau vang', 'màu vàng', 'vàng', 'yellow', 'vang'],
    'Nâu': ['mau nau', 'màu nâu', 'nâu', 'brown', 'nau'],
    'Xám': ['mau xam', 'màu xám', 'xám', 'grey', 'gray', 'xam'],
    'Cam': ['mau cam', 'màu cam', 'cam', 'orange'],
    'Tím': ['mau tim', 'màu tím', 'tím', 'purple', 'tim']
}

MATERIALS = {
    'Jean': ['jean', 'bò', 'denim', 'bo'],
    'Cotton': ['cotton', 'thun'],
    'Lụa': ['lụa', 'silk', 'lua'],
    'Da': [' da ', 'da bò', 'da thật', 'leather'],
    'Len': ['len', 'wool'],
    'Polyester': ['polyester', 'poly', 'nỉ', 'spandex', 'ni'],
    'Kaki': ['kaki', 'khaki'],
    'Linen': ['linen', 'đũi', 'dui']
}

def extract_color(name, description):
    name_lower = name.lower() if name else ""
    desc_lower = description.lower() if description else ""
    for color, keywords in COLORS.items():
        for kw in keywords:
            if kw in name_lower or kw in desc_lower:
                return color
    return None

def extract_material(name, description):
    name_lower = name.lower() if name else ""
    desc_lower = description.lower() if description else ""
    for material, keywords in MATERIALS.items():
        for kw in keywords:
            if kw in name_lower or kw in desc_lower:
                return material
    return None

def main():
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 60)
    print("REBUILDING GRAPH SCHEMA (Giai đoạn 2.1)")
    print("=" * 60)
    print(f"Connecting to Neo4j at {NEO4J_URI}...")
    
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    except Exception as e:
        print(f"Cannot connect to Neo4j: {e}")
        return

    with driver.session() as session:
        # Create indexes for the new nodes
        print("Creating constraints and indexes...")
        session.run("CREATE INDEX color_name IF NOT EXISTS FOR (c:Color) ON (c.name)")
        session.run("CREATE INDEX material_name IF NOT EXISTS FOR (m:Material) ON (m.name)")
        
        # Get all products
        print("Fetching product nodes...")
        result = session.run("MATCH (p:Product) RETURN p.id AS id, p.name AS name, p.brand AS brand, p.description AS description, p.price AS price")
        products = list(result)
        print(f"Found {len(products)} products in Neo4j.")

        color_count = 0
        material_count = 0
        brand_count = 0

        for record in products:
            pid = record['id']
            name = record['name'] or ""
            brand = record['brand'] or ""
            description = record['description'] or ""
            
            # Extract color and material
            color = extract_color(name, description)
            material = extract_material(name, description)
            
            # 1. Merge Brand node and link
            if brand:
                session.run("""
                    MATCH (p:Product {id: $pid})
                    MERGE (b:Brand {name: $brand})
                    MERGE (p)-[:MADE_BY]->(b)
                """, pid=pid, brand=brand)
                brand_count += 1
                
            # 2. Merge Color node and link
            if color:
                session.run("""
                    MATCH (p:Product {id: $pid})
                    MERGE (c:Color {name: $color})
                    MERGE (p)-[:HAS_COLOR]->(c)
                """, pid=pid, color=color)
                color_count += 1
                
            # 3. Merge Material node and link
            if material:
                session.run("""
                    MATCH (p:Product {id: $pid})
                    MERGE (m:Material {name: $material})
                    MERGE (p)-[:HAS_MATERIAL]->(m)
                """, pid=pid, material=material)
                material_count += 1

            # 4. Set default active status and positive stock count for legacy products if not already set
            session.run("""
                MATCH (p:Product {id: $pid})
                SET p.status = coalesce(p.status, 'active'),
                    p.stock_quantity = coalesce(p.stock_quantity, 100)
            """, pid=pid)

        print("\nRestructuring Summary:")
        print(f"  - Products analyzed: {len(products)}")
        print(f"  - Brand nodes linked: {brand_count}")
        print(f"  - Color nodes created/linked: {color_count}")
        print(f"  - Material nodes created/linked: {material_count}")
        print(f"  - Status & stock set to active/100 for legacy products")
        print("\nRestructuring complete!")
        
    driver.close()

if __name__ == '__main__':
    main()
