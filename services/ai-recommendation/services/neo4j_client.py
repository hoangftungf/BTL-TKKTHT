"""
Neo4j Client for AI Recommendation Service
Provides reusable connection and utility functions for Neo4j graph database
"""

import os
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Singleton driver instance
_driver = None


def get_driver():
    """
    Get or create Neo4j driver (singleton pattern)

    Configuration from environment:
    - NEO4J_URI: Connection URI (default: bolt://neo4j:7687)
    - NEO4J_USER: Username (default: neo4j)
    - NEO4J_PASSWORD: Password (default: password123)

    Returns:
        Neo4j driver instance or None if connection fails
    """
    global _driver

    if _driver is not None:
        return _driver

    try:
        from neo4j import GraphDatabase

        uri = os.environ.get('NEO4J_URI', 'bolt://neo4j:7687')
        user = os.environ.get('NEO4J_USER', 'neo4j')
        password = os.environ.get('NEO4J_PASSWORD', 'password123')

        _driver = GraphDatabase.driver(uri, auth=(user, password))

        # Verify connection
        _driver.verify_connectivity()
        logger.info(f"Connected to Neo4j at {uri}")

        return _driver

    except ImportError:
        logger.error("neo4j package not installed. Run: pip install neo4j")
        return None
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        return None


def close_driver():
    """Close the Neo4j driver"""
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
        logger.info("Neo4j driver closed")


@contextmanager
def get_session():
    """
    Context manager for Neo4j session

    Usage:
        with get_session() as session:
            session.run("MATCH (n) RETURN n LIMIT 10")
    """
    driver = get_driver()
    if driver is None:
        raise ConnectionError("Cannot connect to Neo4j")

    session = driver.session()
    try:
        yield session
    finally:
        session.close()


def run_query(query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict]:
    """
    Execute a Cypher query and return results as list of dicts

    Args:
        query: Cypher query string
        parameters: Optional query parameters

    Returns:
        List of result records as dictionaries
    """
    with get_session() as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]


def run_query_single(query: str, parameters: Optional[Dict[str, Any]] = None) -> Optional[Dict]:
    """
    Execute a Cypher query and return single result

    Args:
        query: Cypher query string
        parameters: Optional query parameters

    Returns:
        Single result record as dictionary, or None
    """
    with get_session() as session:
        result = session.run(query, parameters or {})
        record = result.single()
        return record.data() if record else None


def create_indexes():
    """Create recommended indexes for the graph schema"""
    indexes = [
        "CREATE INDEX user_id IF NOT EXISTS FOR (u:User) ON (u.id)",
        "CREATE INDEX product_id IF NOT EXISTS FOR (p:Product) ON (p.id)",
        "CREATE INDEX category_name IF NOT EXISTS FOR (c:Category) ON (c.name)",
        "CREATE INDEX brand_name IF NOT EXISTS FOR (b:Brand) ON (b.name)",
    ]

    with get_session() as session:
        for index_query in indexes:
            try:
                session.run(index_query)
            except Exception as e:
                logger.warning(f"Index creation warning: {e}")

    logger.info("Neo4j indexes created/verified")


def clear_graph():
    """Clear all nodes and relationships (use with caution!)"""
    with get_session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    logger.warning("Neo4j graph cleared")


def get_stats() -> Dict[str, int]:
    """Get graph statistics"""
    with get_session() as session:
        # Count nodes by label
        users = session.run("MATCH (u:User) RETURN COUNT(u) AS count").single()['count']
        products = session.run("MATCH (p:Product) RETURN COUNT(p) AS count").single()['count']
        categories = session.run("MATCH (c:Category) RETURN COUNT(c) AS count").single()['count']

        # Count relationships
        relationships = session.run("MATCH ()-[r]->() RETURN COUNT(r) AS count").single()['count']

        return {
            'users': users,
            'products': products,
            'categories': categories,
            'total_relationships': relationships
        }
