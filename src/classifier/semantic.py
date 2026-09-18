"""
Semantic classifier using sentence embeddings + cosine similarity.
Runs on CPU in ~50ms per request. No LLM needed.
"""
import numpy as np
from sentence_transformers import SentenceTransformer
from src.classifier.policy_examples import POLICY_EXAMPLES
from src.ingestion.normalizer import normalize_text


_MODEL = None
_CENTROIDS = None
_CATEGORIES = None


def _get_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL


def _get_centroids():
    """Compute category centroids once. Cache them in memory."""
    global _CENTROIDS, _CATEGORIES
    if _CENTROIDS is None:
        model = _get_model()
        centroids = []
        categories = []
        for category, examples in POLICY_EXAMPLES.items():
            embeddings = model.encode(examples, normalize_embeddings=True)
            centroid = embeddings.mean(axis=0)
            # Re-normalize after averaging
            centroid = centroid / np.linalg.norm(centroid)
            centroids.append(centroid)
            categories.append(category)
        _CENTROIDS = np.array(centroids)
        _CATEGORIES = categories
    return _CENTROIDS, _CATEGORIES


def classify(text: str) -> dict:
    """
    Return a similarity score to each policy category.
    
    Output shape:
    {
        "scores": {"hate_speech": 0.42, "harassment": 0.71, ...},
        "top_category": "harassment",
        "top_score": 0.71,
        "confidence": "high" | "medium" | "low"
    }
    """
    
    text = normalize_text(text)
    model = _get_model()
    centroids, categories = _get_centroids()

    embedding = model.encode([text], normalize_embeddings=True)[0]
    similarities = centroids @ embedding  # cosine similarity

    scores = {cat: float(sim) for cat, sim in zip(categories, similarities)}
    top_idx = int(np.argmax(similarities))
    top_category = categories[top_idx]
    top_score = float(similarities[top_idx])

    return {
        "scores": scores,
        "top_category": top_category,
        "top_score": top_score,
        "confidence": _confidence(top_score),
    }


def _confidence(top_score: float) -> str:
    """Map a similarity score to a confidence band."""
    if top_score >= 0.65:
        return "high"
    if top_score >= 0.45:
        return "medium"
    return "low"


def score_to_flag(classification: dict) -> str:
    """
    Convert a classification to a flag based on category and score.
    Uses per-category thresholds — different categories have different sensitivities.
    """
    top = classification["top_category"]
    score = classification["top_score"]

    # Per-category thresholds (calibrated by hand for now; learned later)
    thresholds = {
        "hate_speech": {"red": 0.55, "yellow": 0.40},   # low → catch more
        "threat":      {"red": 0.55, "yellow": 0.40},
        "harassment":  {"red": 0.60, "yellow": 0.45},
        "sexual":      {"red": 0.60, "yellow": 0.45},
        "illegal":     {"red": 0.55, "yellow": 0.40},
        "spam":        {"red": 0.70, "yellow": 0.55},   # high → fewer false positives
        "benign":      {"red": 1.01, "yellow": 1.01},   # never flags as violation
    }

    t = thresholds.get(top, {"red": 0.6, "yellow": 0.45})

    if top == "benign":
        return "GREEN"
    if score >= t["red"]:
        return "RED"
    if score >= t["yellow"]:
        return "YELLOW"
    return "GREEN"