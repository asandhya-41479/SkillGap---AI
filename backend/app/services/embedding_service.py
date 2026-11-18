import logging
from functools import lru_cache

import numpy as np

logger = logging.getLogger(__name__)

# The same all-MiniLM-L6-v2 model as before, run through ONNX Runtime (fastembed) instead of
# PyTorch (sentence-transformers). Same weights, same 384-dim vectors, so the similarity
# thresholds validated in Module 4 still apply. Why: PyTorch pushed the server over the
# 512 MB limit of the free hosting plan ("Ran out of memory" on Render); ONNX needs far less.
_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_THREADS = 1  # one CPU thread: lower memory, and the free plan has a fraction of a CPU anyway


class EmbeddingServiceUnavailable(Exception):
    """Raised when the embedding model failed to load or encode."""


class EmbeddingService:
    """
    Thin wrapper around a single, process-wide embedding model.

    - Loads the model once (lazy, on first use), so the server starts small and fast.
    - Caches embeddings per canonical skill string so repeated requirement/skill
      comparisons never re-embed the same text.
    - Fails loudly with EmbeddingServiceUnavailable rather than crashing the
      request pipeline with a raw exception, so callers (the matching engine)
      can catch this one type and fall back safely (Step 1 §10 / §20).
    """

    def __init__(self) -> None:
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                from fastembed import TextEmbedding   # imported here: nothing heavy loads at startup

                logger.info("Loading embedding model: %s", _MODEL_NAME)
                self._model = TextEmbedding(model_name=_MODEL_NAME, threads=_THREADS)
            except Exception as exc:  # model download/load failure, disk, memory, etc.
                logger.exception("Failed to load embedding model")
                raise EmbeddingServiceUnavailable(str(exc)) from exc
        return self._model

    @lru_cache(maxsize=2048)
    def _embed_cached(self, text: str) -> tuple[float, ...]:
        """
        Cached at the text level (the canonical 'skill (category)' string).
        Returns a plain tuple (hashable, cache-friendly) of a unit-length vector.
        """
        model = self._load_model()
        try:
            vector = np.asarray(next(iter(model.embed([text]))), dtype=np.float32)
        except Exception as exc:
            logger.exception("Embedding generation failed for text=%r", text)
            raise EmbeddingServiceUnavailable(str(exc)) from exc
        norm = float(np.linalg.norm(vector))
        if norm == 0.0:
            raise EmbeddingServiceUnavailable("Model returned an empty vector.")
        return tuple(float(x) for x in vector / norm)

    def embed(self, text: str) -> np.ndarray:
        """Public entry point — returns a numpy array, cache is transparent to callers."""
        return np.array(self._embed_cached(text))

    def cosine_similarity(self, text_a: str, text_b: str) -> float:
        """
        Vectors are normalized (unit length), so cosine similarity
        reduces to a plain dot product.
        """
        vec_a = self.embed(text_a)
        vec_b = self.embed(text_b)
        return float(np.dot(vec_a, vec_b))


# Process-wide singleton — import this instance, don't instantiate EmbeddingService yourself.
embedding_service = EmbeddingService()
