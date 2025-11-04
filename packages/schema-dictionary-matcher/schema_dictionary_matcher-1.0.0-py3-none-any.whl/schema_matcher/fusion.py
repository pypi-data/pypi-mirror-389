"""
Fusion methods for combining dense and sparse retrieval
"""

import logging
from typing import List, Tuple, Dict
import numpy as np


class ConvexCombinationFusion:
    """
    Convex combination fusion for dense and sparse retrieval.

    Score = alpha * dense_score + (1 - alpha) * sparse_score

    Based on research showing 2-5% improvement over RRF.
    Optimal alpha typically 0.6-0.7.
    """

    def __init__(self, alpha: float = 0.65):
        self.alpha = alpha
        self.logger = logging.getLogger(__name__)

    def fuse(
            self,
            dense_results: List[Tuple[str, float]],
            sparse_results: List[Tuple[str, float]],
            top_k: int = 100
    ) -> List[Tuple[str, float]]:
        """
        Fuse dense and sparse results.

        Args:
            dense_results: List of (id, score) from dense retrieval
            sparse_results: List of (id, score) from sparse retrieval
            top_k: Number of results to return

        Returns:
            List of (id, fused_score) tuples
        """
        # Normalize scores to [0, 1]
        dense_dict = self._normalize_scores(dense_results)
        sparse_dict = self._normalize_scores(sparse_results)

        # Get all unique IDs
        all_ids = set(dense_dict.keys()) | set(sparse_dict.keys())

        # Compute fused scores
        fused_scores = {}
        for doc_id in all_ids:
            dense_score = dense_dict.get(doc_id, 0.0)
            sparse_score = sparse_dict.get(doc_id, 0.0)

            fused_score = self.alpha * dense_score + (1 - self.alpha) * sparse_score
            fused_scores[doc_id] = fused_score

        # Sort by score
        sorted_results = sorted(
            fused_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_results[:top_k]

    def _normalize_scores(
            self,
            results: List[Tuple[str, float]]
    ) -> Dict[str, float]:
        """Normalize scores to [0, 1] using min-max scaling."""
        if not results:
            return {}

        scores = [score for _, score in results]
        min_score = min(scores)
        max_score = max(scores)

        if max_score == min_score:
            # All scores are the same
            return {doc_id: 1.0 for doc_id, _ in results}

        normalized = {}
        for doc_id, score in results:
            norm_score = (score - min_score) / (max_score - min_score)
            normalized[doc_id] = norm_score

        return normalized


class ReciprocalRankFusion:
    """
    Reciprocal Rank Fusion (RRF) for combining rankings.

    Included for comparison - convex combination typically performs better.
    """

    def __init__(self, k: int = 60):
        self.k = k

    def fuse(
            self,
            dense_results: List[Tuple[str, float]],
            sparse_results: List[Tuple[str, float]],
            top_k: int = 100
    ) -> List[Tuple[str, float]]:
        """Fuse using RRF."""
        # Convert to rankings
        dense_ranks = {doc_id: rank for rank, (doc_id, _) in enumerate(dense_results, 1)}
        sparse_ranks = {doc_id: rank for rank, (doc_id, _) in enumerate(sparse_results, 1)}

        # Get all IDs
        all_ids = set(dense_ranks.keys()) | set(sparse_ranks.keys())

        # Compute RRF scores
        rrf_scores = {}
        for doc_id in all_ids:
            dense_rank = dense_ranks.get(doc_id, len(dense_results) + 1)
            sparse_rank = sparse_ranks.get(doc_id, len(sparse_results) + 1)

            rrf_score = (1 / (self.k + dense_rank)) + (1 / (self.k + sparse_rank))
            rrf_scores[doc_id] = rrf_score

        # Sort by score
        sorted_results = sorted(
            rrf_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_results[:top_k]