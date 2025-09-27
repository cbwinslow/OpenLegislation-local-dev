"""GPU-aware embedding service for bill text."""
from __future__ import annotations

import logging
import os
from typing import Iterable, List, Optional

try:  # optional heavy deps
    import torch
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover
    torch = None
    SentenceTransformer = None

logger = logging.getLogger(__name__)


class EmbeddingService:
    _instance: Optional["EmbeddingService"] = None

    def __init__(self, model_name: str):
        if SentenceTransformer is None:
            raise RuntimeError("sentence-transformers not installed")
        self.device = "cuda" if torch and torch.cuda.is_available() else "cpu"
        if self.device == "cpu" and os.getenv("FORCE_GPU_EMBEDDINGS") == "true":
            logger.warning("CUDA not available; falling back to CPU embeddings")
        self.model = SentenceTransformer(model_name)
        if self.device == "cuda":
            self.model = self.model.to(self.device)

    @classmethod
    def instance(cls) -> Optional["EmbeddingService"]:
        if not os.getenv("ENABLE_EMBEDDINGS"):
            return None
        if cls._instance is not None:
            return cls._instance
        model_name = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        try:
            cls._instance = EmbeddingService(model_name)
        except Exception as exc:  # pragma: no cover - initialization failure
            logger.warning("Embedding model unavailable: %s", exc)
            cls._instance = None
        return cls._instance

    def embed(self, texts: Iterable[str]) -> List[List[float]]:
        embeddings = self.model.encode(
            list(texts),
            convert_to_numpy=True,
            device=self.device if torch else None,
            normalize_embeddings=False,
        )
        return [vec.tolist() for vec in embeddings]
