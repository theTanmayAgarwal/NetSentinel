"""Embedding service for network configuration commands.

Supports sentence-transformers (all-MiniLM-L6-v2) when available, and falls back
to a deterministic n-gram hashing embedder when sentence-transformers is absent.
Always returns unit-normalized 384-dimensional numpy vectors suitable for cosine
similarity calculation via dot product.
"""
from __future__ import annotations

import math
import re
from typing import List
import numpy as np

# Optional ML import
_ST_MODEL = None
_ST_ATTEMPTED = False


def _get_sentence_transformer():
    global _ST_MODEL, _ST_ATTEMPTED
    if not _ST_ATTEMPTED:
        _ST_ATTEMPTED = True
        try:
            from sentence_transformers import SentenceTransformer
            _ST_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            _ST_MODEL = None
    return _ST_MODEL


def _offline_fallback_embed(text: str, dim: int = 384) -> List[float]:
    """Deterministic feature hashing embedder for offline/lightweight execution."""
    vec = np.zeros(dim, dtype=np.float32)
    # Tokenize command into tokens and character 3-grams
    tokens = re.findall(r"\w+", text.lower())
    ngrams = [text[i : i + 3].lower() for i in range(len(text) - 2)]
    features = tokens + ngrams

    for feat in features:
        # Simple string hash to vector index map
        h = sum(ord(c) * (31 ** idx) for idx, c in enumerate(feat))
        idx = h % dim
        sign = 1.0 if (h % 2) == 0 else -1.0
        vec[idx] += sign

    norm = np.linalg.norm(vec)
    if norm > 1e-9:
        vec = vec / norm
    else:
        vec[0] = 1.0
    return vec.tolist()


def get_embedding(text: str) -> List[float]:
    """Generate a unit-normalized vector embedding for a configuration command."""
    text = text.strip()
    if not text:
        return [0.0] * 384

    model = _get_sentence_transformer()
    if model is not None:
        try:
            vec = model.encode(text, normalize_embeddings=True)
            return vec.tolist()
        except Exception:
            pass

    return _offline_fallback_embed(text, dim=384)


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calculate cosine similarity between two embedding vectors."""
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a < 1e-9 or norm_b < 1e-9:
        return 0.0
    similarity = float(np.dot(a, b) / (norm_a * norm_b))
    return max(0.0, min(1.0, similarity))
