"""
brain/semantic_matcher.py
Lightweight semantic similarity engine for Aether.
Uses all-MiniLM-L6-v2 (22MB) to match user intent to known skills.
"""
from __future__ import annotations

_model = None  # Lazy-loaded singleton

def _get_model():
    """Lazy-load the sentence transformer model to avoid slow startup."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            print("[Aether/Brain] Loading semantic model...", flush=True)
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            print("[Aether/Brain] Semantic model ready.", flush=True)
        except ImportError:
            print("[Aether/Brain] sentence-transformers not installed. Semantic matching disabled.")
            _model = "UNAVAILABLE"
    return _model if _model != "UNAVAILABLE" else None


def find_best_skill(query: str, skills: dict, threshold: float = 0.45) -> tuple[str | None, str | None, float]:
    """
    Finds the best matching skill for a given user query using cosine similarity.

    Args:
        query:     The raw user input (e.g. "launch the music player")
        skills:    Dict of {app_name: url} from the registry/predefined skills
        threshold: Minimum similarity score to accept a match (0.0 to 1.0)

    Returns:
        (best_name, best_url, score) — or (None, None, 0.0) if no match found
    """
    model = _get_model()
    if model is None or not skills:
        return None, None, 0.0

    try:
        from sentence_transformers.util import cos_sim
        import torch

        skill_names = list(skills.keys())
        
        # Encode the query and all skill names
        query_embedding = model.encode(query, convert_to_tensor=True)
        skill_embeddings = model.encode(skill_names, convert_to_tensor=True)
        
        # Calculate cosine similarities
        similarities = cos_sim(query_embedding, skill_embeddings)[0]
        best_idx = int(similarities.argmax())
        best_score = float(similarities[best_idx])
        
        if best_score >= threshold:
            best_name = skill_names[best_idx]
            return best_name, skills[best_name], best_score

        return None, None, best_score

    except Exception as e:
        print(f"[Aether/Brain] Semantic match error: {e}")
        return None, None, 0.0
