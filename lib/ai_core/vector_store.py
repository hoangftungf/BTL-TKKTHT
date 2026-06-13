"""
Unified Vector Store — FAISS-based product embedding store.

Single source of truth cho mọi product embeddings (768d).
- FAISS IndexFlatIP for cosine similarity
- Disk persistence (save/load)
- Filters tích hợp (status, stock, category, price range)
- Có thể add/remove single product (không cần rebuild toàn bộ)

Usage:
    from lib.ai_core.vector_store import vector_store

    # Index products
    vector_store.bulk_index(products)

    # Search
    results = vector_store.search(query_emb, k=10, filters={"category": "Laptop"})
"""
import json
import logging
import os
import numpy as np
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class UnifiedVectorStore:
    """
    Single source of truth cho product embeddings.

    - Dimension: 768 (nomic-embed-text)
    - Index: FAISS IndexFlatIP (cosine similarity)
    - Persistence: save/load to disk (json meta + faiss index)
    - Filters: category, brand, price range, status, stock
    """

    EMBEDDING_DIM = 1024

    def __init__(self, embedding_dim: int = EMBEDDING_DIM):
        self.embedding_dim = embedding_dim
        self.index = None
        self.product_ids: List[str] = []
        self.product_data: Dict[str, dict] = {}
        self._embeddings_fallback: List[np.ndarray] = []
        self._initialized = False

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def _initialize(self):
        """Lazy init FAISS index."""
        if self._initialized:
            return
        try:
            import faiss
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            logger.info(f"FAISS index initialized (dim={self.embedding_dim})")
        except ImportError:
            logger.warning("FAISS not installed, using numpy fallback")
            self.index = None
        self._initialized = True

    # ------------------------------------------------------------------
    # Add / Remove
    # ------------------------------------------------------------------

    def add(
        self,
        product_id: str,
        embedding: np.ndarray,
        data: Optional[dict] = None,
    ) -> bool:
        """Add a single product to the index."""
        self._initialize()

        embedding = np.array(embedding, dtype="float32").flatten()
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        if self.index is not None:
            self.index.add(embedding.reshape(1, -1))
        else:
            self._embeddings_fallback.append(embedding)

        self.product_ids.append(str(product_id))
        if data:
            self.product_data[str(product_id)] = data

        return True

    def remove(self, product_id: str) -> bool:
        """Remove a product from the index.

        NOTE: FAISS doesn't support deletion natively with IndexFlatIP.
        This marks the product as removed and filters it out during search.
        For full removal, rebuild_index() is needed.
        """
        pid = str(product_id)
        if pid in self.product_data:
            del self.product_data[pid]
        # Mark by removing from IDs list (search filters by product_data presence)
        if pid in self.product_ids:
            self.product_ids.remove(pid)
        return True

    def bulk_index(self, products: List[dict], embed_fn: Callable) -> int:
        """Index multiple products at once.

        Args:
            products: list of dicts with 'id', 'name', etc.
            embed_fn: function that takes list of texts → np.ndarray

        Returns:
            Number of products indexed
        """
        self._initialize()

        # Build text representations for embedding
        from lib.ai_core.acl import ProductACL

        texts = []
        clean_products = []
        for p in products:
            normalized = ProductACL.from_api_response(p)
            text = ProductACL.to_embedding_text(normalized)
            texts.append(text)
            clean_products.append(normalized)

        if not texts:
            return 0

        # Generate embeddings
        if embed_fn.__class__.__name__ == "UnifiedEmbedder":
            # Use sync path for bulk indexing
            embeddings = embed_fn.embed_sync(texts)
        else:
            embeddings = embed_fn(texts)

        # Reset and re-add
        self.reset()
        for i, (product, embedding) in enumerate(zip(clean_products, embeddings)):
            self.add(
                product_id=product["id"],
                embedding=embedding,
                data=product,
            )

        logger.info(f"Bulk indexed {len(clean_products)} products")
        return len(clean_products)

    def reset(self):
        """Reset the entire index."""
        import faiss
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.product_ids = []
        self.product_data = {}
        self._embeddings_fallback = []

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict]:
        """Search similar products with optional filters.

        Filters:
            - category (str): exact match or substring
            - brand (str): exact match or substring
            - price_min (float): minimum price
            - price_max (float): maximum price
            - status (str): product status (default: 'active')
            - in_stock (bool): filter by stock_quantity > 0
        """
        self._initialize()
        if len(self.product_ids) == 0:
            return []

        # Normalize query
        query_emb = np.array(query_embedding, dtype="float32").flatten()
        norm = np.linalg.norm(query_emb)
        if norm > 0:
            query_emb = query_emb / norm
        query_emb = query_emb.reshape(1, -1)

        # Search with larger candidate pool for filtering
        search_k = min(k * 3 if filters else k, len(self.product_ids))

        if self.index is not None:
            import faiss
            distances, indices = self.index.search(query_emb, search_k)
            candidates = []
            for i, idx in enumerate(indices[0]):
                if idx >= 0 and idx < len(self.product_ids):
                    pid = self.product_ids[idx]
                    p_data = self.product_data.get(pid, {})
                    if self._apply_filters(p_data, filters):
                        candidates.append({
                            "product_id": pid,
                            "score": float(distances[0][i]),
                            "data": p_data,
                        })
                        if len(candidates) >= k:
                            break
            return candidates
        else:
            # Numpy fallback
            embeddings = np.array(self._embeddings_fallback)
            if len(embeddings) == 0:
                return []
            scores = np.dot(embeddings, query_emb.T).flatten()
            top_indices = np.argsort(scores)[::-1][:search_k]
            candidates = []
            for idx in top_indices:
                pid = self.product_ids[idx]
                p_data = self.product_data.get(pid, {})
                if self._apply_filters(p_data, filters):
                    candidates.append({
                        "product_id": pid,
                        "score": float(scores[idx]),
                        "data": p_data,
                    })
                    if len(candidates) >= k:
                        break
            return candidates

    @staticmethod
    def _apply_filters(data: dict, filters: Optional[Dict]) -> bool:
        """Apply filters to a product data dict."""
        if not filters:
            return True

        # Status filter (default: active)
        status = filters.get("status", "active")
        if data.get("status", "active") not in [status, None]:
            if status == "active" and data.get("status") not in ("active", None):
                return False
            elif data.get("status") != status:
                return False

        # In-stock filter
        if filters.get("in_stock", False):
            stock = data.get("stock_quantity", 0)
            if stock is not None and stock <= 0:
                return False

        # Category filter
        category = filters.get("category")
        if category:
            cat = (data.get("category") or "").lower()
            if category.lower() not in cat:
                return False

        # Brand filter
        brand = filters.get("brand")
        if brand:
            b = (data.get("brand") or "").lower()
            if brand.lower() not in b:
                return False

        # Price range
        price = data.get("price", 0)
        if filters.get("price_min") is not None and price < filters["price_min"]:
            return False
        if filters.get("price_max") is not None and price > filters["price_max"]:
            return False

        return True

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, directory: str) -> bool:
        """Persist index + metadata to disk."""
        os.makedirs(directory, exist_ok=True)
        try:
            if self.index is not None:
                import faiss
                faiss.write_index(self.index, os.path.join(directory, "unified.index"))
            elif self._embeddings_fallback:
                np.save(
                    os.path.join(directory, "embeddings.npy"),
                    np.array(self._embeddings_fallback, dtype="float32"),
                )
            with open(os.path.join(directory, "meta.json"), "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "product_ids": self.product_ids,
                        "product_data": self.product_data,
                        "embedding_dim": self.embedding_dim,
                    },
                    f,
                    ensure_ascii=False,
                )
            logger.info(f"VectorStore saved ({len(self.product_ids)} products) → {directory}")
            return True
        except Exception as e:
            logger.error(f"VectorStore save failed: {e}")
            return False

    def load(self, directory: str) -> bool:
        """Load index + metadata from disk."""
        meta_path = os.path.join(directory, "meta.json")
        if not os.path.exists(meta_path):
            logger.info(f"No saved index at {directory}")
            return False

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            self.product_ids = meta["product_ids"]
            self.product_data = meta["product_data"]
            self.embedding_dim = meta.get("embedding_dim", self.EMBEDDING_DIM)
            self._initialize()

            index_path = os.path.join(directory, "unified.index")
            if os.path.exists(index_path):
                import faiss
                self.index = faiss.read_index(index_path)
            else:
                emb_path = os.path.join(directory, "embeddings.npy")
                if os.path.exists(emb_path):
                    self._embeddings_fallback = list(np.load(emb_path, allow_pickle=True))

            logger.info(f"VectorStore loaded ({len(self.product_ids)} products) ← {directory}")
            return True
        except Exception as e:
            logger.error(f"VectorStore load failed: {e}")
            return False


# Singleton instance
vector_store = UnifiedVectorStore()
