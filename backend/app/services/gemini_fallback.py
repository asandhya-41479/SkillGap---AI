"""Shared Gemini model chain for Modules 3 and 4 (same models and order as Modules 5 and 6).

When one model is overloaded (503 "high demand") or failing, the next model is tried, because each model has
its own capacity. Only if every model fails is the last error raised, so each caller keeps its existing
fallback (Module 3: clear 502 error, Module 4: deterministic template explanation).
"""
import logging

logger = logging.getLogger(__name__)

MODELS = ("gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite")


def generate_with_fallback(client, prompt: str, **kwargs):
    """Returns the first successful generate_content response. Raises the last error if all models fail."""
    last_error = None
    for model in MODELS:
        try:
            return client.models.generate_content(model=model, contents=prompt, **kwargs)
        except Exception as e:  # 503 overload, 429 quota, network: try the next model
            last_error = e
            logger.warning("Gemini model %s failed (%s); trying the next model", model, type(e).__name__)
    raise last_error
