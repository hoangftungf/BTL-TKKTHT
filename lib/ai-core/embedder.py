"""
Unified Text Embedder — dùng chung cho mọi AI services.

Sử dụng nomic-embed-text (768d) qua Ollama API.
Fallback: TF-IDF (sklearn) khi Ollama không available.

Usage:
    from lib.ai_core.embedder import embedder

    # Batch async
    embeddings = await embedder.embed(["text1", "text2"])

    # Sync fallback
    embeddings = embedder.embed_sync(["text1", "text2"])
"""
import logging
import numpy as np
import httpx
from typing import List, Optional, Union
from django.conf import settings

logger = logging.getLogger(__name__)


class UnifiedEmbedder:
    """
    Unified Text Embedder.

    - Primary: nomic-embed-text (768d) via Ollama /api/embed
    - Fallback: TF-IDF (max_features=768)
    - Batch processing với configurable batch_size
    """

    MODEL_NAME = "bge-m3"
    EMBEDDING_DIM = 1024

    def __init__(self, ollama_host: Optional[str] = None):
        self.ollama_host = ollama_host or getattr(
            settings, "OLLAMA_HOST", "http://ollama:11434"
        )
        self._tfidf = None
        self._tfidf_fitted = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def embed(
        self, texts: Union[str, List[str]], batch_size: int = 10
    ) -> np.ndarray:
        """Async batch embedding via Ollama (nomic-embed-text)."""
        if isinstance(texts, str):
            texts = [texts]
        if not texts:
            return np.array([])

        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(
                        f"{self.ollama_host}/api/embed",
                        json={"model": self.MODEL_NAME, "input": batch},
                    )
                if response.status_code == 200:
                    emb_list = response.json().get("embeddings", [])
                    for emb in emb_list:
                        all_embeddings.append(emb if emb else [0.0] * self.EMBEDDING_DIM)
                else:
                    logger.warning(f"Ollama embed status {response.status_code}")
                    all_embeddings.extend([[0.0] * self.EMBEDDING_DIM] * len(batch))
            except Exception as e:
                logger.warning(f"Ollama embed failed (batch {i}): {e}")
                # Fallback to sync for this batch
                sync_embs = self.embed_sync(batch)
                if len(sync_embs) > 0:
                    all_embeddings.extend(sync_embs)
                else:
                    all_embeddings.extend([[0.0] * self.EMBEDDING_DIM] * len(batch))

        return np.array(all_embeddings)

    def embed_sync(
        self, texts: Union[str, List[str]]
    ) -> np.ndarray:
        """Sync embedding — thử Ollama trước, fallback TF-IDF."""
        if isinstance(texts, str):
            texts = [texts]
        if not texts:
            return np.array([])

        # Try Ollama
        try:
            response = httpx.post(
                f"{self.ollama_host}/api/embed",
                json={"model": self.MODEL_NAME, "input": texts},
                timeout=120.0,
            )
            if response.status_code == 200:
                emb_list = response.json().get("embeddings", [])
                return np.array([
                    emb if emb else [0.0] * self.EMBEDDING_DIM
                    for emb in emb_list
                ])
        except Exception as e:
            logger.warning(f"Ollama sync embed failed: {e}")

        # Fallback: TF-IDF
        return self._tfidf_embed(texts)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _tfidf_embed(self, texts: List[str]) -> np.ndarray:
        """TF-IDF fallback embedding."""
        from sklearn.feature_extraction.text import TfidfVectorizer

        if self._tfidf is None:
            self._tfidf = TfidfVectorizer(max_features=self.EMBEDDING_DIM)
        try:
            if self._tfidf_fitted:
                return self._tfidf.transform(texts).toarray()
            else:
                result = self._tfidf.fit_transform(texts).toarray()
                self._tfidf_fitted = True
                return result
        except Exception as e:
            logger.error(f"TF-IDF error: {e}")
            return np.zeros((len(texts), self.EMBEDDING_DIM))

    def normalize(self, embedding: np.ndarray) -> np.ndarray:
        """L2 normalize embedding vector."""
        norm = np.linalg.norm(embedding)
        if norm > 0:
            return embedding / norm
        return embedding


# Singleton instance
embedder = UnifiedEmbedder()
