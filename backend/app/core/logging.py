"""One logging format for the whole backend, so Render's logs show time, level and module."""
import logging

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    if any(getattr(h, "_skillgap", False) for h in root.handlers):
        return  # already configured (e.g. reloaded in tests)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(_FORMAT))
    handler._skillgap = True
    root.addHandler(handler)
    root.setLevel(level)
    # Third-party libraries are noisy at INFO; keep their warnings and errors only.
    for noisy in ("httpx", "httpcore", "urllib3", "huggingface_hub", "google_genai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
