"""Shared embedding model singleton — loaded once, used everywhere."""
from __future__ import annotations

_model = None

def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print("[Aether/Brain] Loading embedding model...", flush=True)
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print("[Aether/Brain] Embedding model ready.", flush=True)
    return _model
