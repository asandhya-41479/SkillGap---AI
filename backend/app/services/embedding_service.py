import logging
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingServiceUnavailable(Exception):
    """Raised when the embedding model failed to load or encode."""


class EmbeddingService:
    """
    Thin wrapper around a single, process-wide SentenceTransformer instance.

    - Loads the model once (lazy, on first use).
    - Caches embeddings per canonical skill string so repeated requirement/skill
      comparisons never re-embed the same text.
    - Fails loudly with EmbeddingServiceUnavailable rather than crashing the
      request pipeline with a raw exception, so callers (the matching engine)
      can catch this one type and fall back safely (Step 1 §10 / §20).
    """

    def __init__(self) -> None:
        self._model: SentenceTransformer | None = None

    def _load_model(self) -> SentenceTransformer:
        if self._model is None:

            try:
                logger.info("Loading embedding model: %s", _MODEL_NAME)
                self._model = SentenceTransformer(_MODEL_NAME)
            except Exception as exc:  # model download/load failure, disk, memory, etc.
                logger.exception("Failed to load embedding model")
                raise EmbeddingServiceUnavailable(str(exc)) from exc
        return self._model

    @lru_cache(maxsize=2048)
    def _embed_cached(self, text: str) -> tuple[float, ...]:
        """
        Cached at the text level (the canonical 'skill (category)' string).
        Returns a plain tuple (hashable, cache-friendly) of a normalized vector.
        """
        model = self._load_model()
        try:
            vector = model.encode(text, normalize_embeddings=True)
        except Exception as exc:
            logger.exception("Embedding generation failed for text=%r", text)
            raise EmbeddingServiceUnavailable(str(exc)) from exc
        return tuple(float(x) for x in vector)

    def embed(self, text: str) -> np.ndarray:
        """Public entry point — returns a numpy array, cache is transparent to callers."""
        return np.array(self._embed_cached(text))

    def cosine_similarity(self, text_a: str, text_b: str) -> float:
        """
        Vectors are already normalized (unit length), so cosine similarity
        reduces to a plain dot product.
        """
        vec_a = self.embed(text_a)

        vec_b = self.embed(text_b)
        return float(np.dot(vec_a, vec_b))


# Process-wide singleton — import this instance, don't instantiate EmbeddingService yourself.
embedding_service = EmbeddingService()