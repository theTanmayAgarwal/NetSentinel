"""Local Vector Store for learned exemplars.

Performs similarity search using cosine similarity over exemplar embeddings.
Supports FAISS when installed, and defaults to NumPy dot-product vector search.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from app.embeddings.embedder import cosine_similarity, get_embedding


class VectorStore:
    def __init__(self, confidence_threshold: float = 0.80) -> None:
        self.confidence_threshold = confidence_threshold

    def search_similar(
        self,
        query_text: str,
        exemplars: List[Dict[str, Any]],
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Search top-k most similar approved exemplars for a query command."""
        if not query_text or not exemplars:
            return []

        query_vec = get_embedding(query_text)
        results: List[Tuple[float, Dict[str, Any]]] = []

        for ex in exemplars:
            # Get existing embedding or generate on the fly
            ex_vec = ex.get("embedding")
            if not ex_vec:
                ex_vec = get_embedding(ex["text"])

            sim = cosine_similarity(query_vec, ex_vec)
            results.append((sim, ex))

        # Sort by similarity descending
        results.sort(key=lambda x: x[0], reverse=True)

        matches = []
        for sim, ex in results[:top_k]:
            match_item = dict(ex)
            match_item["similarity"] = round(sim, 4)
            matches.append(match_item)

        return matches

    def classify_command(
        self,
        query_text: str,
        exemplars: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Classify command based on vector similarity against exemplars.
        
        Returns status ('classified' or 'unknown'), confidence score, top matches,
        and suggested classification fields.
        """
        matches = self.search_similar(query_text, exemplars, top_k=3)
        top_match = matches[0] if matches else None
        similarity = top_match["similarity"] if top_match else 0.0

        is_classified = similarity >= self.confidence_threshold

        return {
            "status": "classified" if is_classified else "unknown",
            "confidence": similarity,
            "confidence_threshold": self.confidence_threshold,
            "top_matches": matches,
            "suggested": {
                "category": top_match.get("category") if top_match else "other_security_controls",
                "parameter": top_match.get("parameter") if top_match else None,
                "expected_value": top_match.get("expected_value") if top_match else None,
                "control_id": top_match.get("control_id") if top_match else None,
                "vendor": top_match.get("vendor") if top_match else None,
            } if top_match else None,
        }
