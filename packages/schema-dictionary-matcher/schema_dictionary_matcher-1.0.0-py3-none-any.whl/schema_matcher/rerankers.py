"""
Reranking components (ColBERT and Cross-Encoder)
"""

import logging
from typing import List, Tuple, Optional
import numpy as np

from .config import AdvancedConfig
from .models import RerankResult


class ColBERTReranker:
    """
    ColBERT multi-vector reranking.

    Note: This is a simplified implementation. For production,
    consider using actual ColBERT models.
    """

    def __init__(self, config: AdvancedConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.model = None

        # Try to load ColBERT model
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(config.colbert_model)
            self.logger.info(f"Loaded ColBERT model: {config.colbert_model}")
        except Exception as e:
            self.logger.warning(f"Failed to load ColBERT model: {e}")

    def rerank(
            self,
            query: str,
            documents: List[str],
            doc_ids: List[str],
            top_k: int = 10
    ) -> List[RerankResult]:
        """
        Rerank documents using ColBERT-style scoring.

        Args:
            query: Query text
            documents: List of document texts
            doc_ids: Document IDs
            top_k: Number of results to return

        Returns:
            List of RerankResult objects
        """
        if self.model is None:
            # Fallback: return documents in original order with dummy scores
            return [
                RerankResult(
                    doc_id=doc_id,
                    score=1.0 - (i / len(documents)),
                    rank=i + 1,
                    original_rank=i + 1
                )
                for i, doc_id in enumerate(doc_ids[:top_k])
            ]

        try:
            # Encode query and documents
            query_embedding = self.model.encode([query], convert_to_numpy=True)[0]
            doc_embeddings = self.model.encode(documents, convert_to_numpy=True)

            # Compute cosine similarities
            from sentence_transformers import util
            scores = util.cos_sim(query_embedding, doc_embeddings)[0].numpy()

            # Sort by score
            sorted_indices = scores.argsort()[::-1]

            results = []
            for new_rank, orig_idx in enumerate(sorted_indices[:top_k], 1):
                results.append(RerankResult(
                    doc_id=doc_ids[orig_idx],
                    score=float(scores[orig_idx]),
                    rank=new_rank,
                    original_rank=orig_idx + 1
                ))

            return results

        except Exception as e:
            self.logger.error(f"ColBERT reranking failed: {e}")
            # Return original order
            return [
                RerankResult(
                    doc_id=doc_id,
                    score=1.0,
                    rank=i + 1,
                    original_rank=i + 1
                )
                for i, doc_id in enumerate(doc_ids[:top_k])
            ]


class CrossEncoderReranker:
    """Cross-encoder for final verification."""

    def __init__(self, config: AdvancedConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.model = None

        # Load cross-encoder
        try:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(
                config.cross_encoder_model,
                max_length=512
            )
            self.logger.info(f"Loaded cross-encoder: {config.cross_encoder_model}")
        except Exception as e:
            self.logger.warning(f"Failed to load cross-encoder: {e}")

    def rerank(
            self,
            query: str,
            candidates: List[Tuple[str, str, float]],
            top_k: Optional[int] = None
    ) -> List[Tuple[str, float]]:
        """
        Rerank candidates using cross-encoder.

        Args:
            query: Query text
            candidates: List of (id, text, previous_score) tuples
            top_k: Number of results to return

        Returns:
            List of (id, score) tuples
        """
        if self.model is None:
            # Fallback: return candidates with original scores
            return [(id, score) for id, _, score in candidates[:top_k]]

        top_k = top_k or self.config.rerank_top_k

        try:
            # Prepare pairs
            pairs = [[query, text] for _, text, _ in candidates]
            ids = [id for id, _, _ in candidates]

            # Score pairs
            scores = self.model.predict(pairs, batch_size=32, show_progress_bar=False)

            # Sort by score
            sorted_indices = np.argsort(scores)[::-1]

            results = [
                (ids[i], float(scores[i]))
                for i in sorted_indices[:top_k]
            ]

            return results

        except Exception as e:
            self.logger.error(f"Cross-encoder reranking failed: {e}")
            return [(id, score) for id, _, score in candidates[:top_k]]