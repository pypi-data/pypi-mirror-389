"""
Semantic caching system
"""

import logging
import hashlib
from typing import List, Optional, Tuple
import numpy as np

from .config import AdvancedConfig
from .models import MatchResult


class SemanticCache:
    """
    Semantic caching for query results.

    Uses MD5 exact match + vector similarity for cache hits.
    Implements LRU eviction policy.
    """

    def __init__(self, config: AdvancedConfig, embedding_model):
        self.config = config
        self.embedding_model = embedding_model
        self.logger = logging.getLogger(__name__)

        # Cache storage
        self.cache = {}  # MD5 -> (embedding, results)
        self.cache_embeddings = []
        self.cache_keys = []

    def _generate_cache_key(self, query: str) -> str:
        """Generate MD5 hash for exact match."""
        return hashlib.md5(query.encode()).hexdigest()

    def get(
            self,
            query: str,
            query_embedding: np.ndarray
    ) -> Optional[List[MatchResult]]:
        """
        Retrieve cached results if available.

        Args:
            query: Query string
            query_embedding: Query embedding

        Returns:
            Cached results if found, None otherwise
        """
        if not self.config.use_semantic_cache:
            return None

        # Try exact match first
        cache_key = self._generate_cache_key(query)
        if cache_key in self.cache:
            self.logger.debug(f"Exact cache hit for: {query[:50]}")
            return self.cache[cache_key][1]

        # Try semantic similarity
        if len(self.cache_embeddings) == 0:
            return None

        cache_embeddings_array = np.vstack(self.cache_embeddings)

        # Compute similarities
        from sentence_transformers import util
        similarities = util.cos_sim(query_embedding, cache_embeddings_array)[0]
        max_sim_idx = similarities.argmax()
        max_sim = similarities[max_sim_idx].item()

        if max_sim >= self.config.cache_similarity_threshold:
            cache_key = self.cache_keys[max_sim_idx]
            self.logger.info(
                f"Semantic cache hit (similarity={max_sim:.3f}) for: {query[:50]}"
            )
            return self.cache[cache_key][1]

        return None

    def set(
            self,
            query: str,
            query_embedding: np.ndarray,
            results: List[MatchResult]
    ):
        """Store query results in cache."""
        if not self.config.use_semantic_cache:
            return

        # Implement LRU eviction
        if len(self.cache) >= self.config.cache_max_size:
            oldest_key = self.cache_keys.pop(0)
            del self.cache[oldest_key]
            self.cache_embeddings.pop(0)

        # Add to cache
        cache_key = self._generate_cache_key(query)
        self.cache[cache_key] = (query_embedding, results)
        self.cache_embeddings.append(query_embedding)
        self.cache_keys.append(cache_key)

        self.logger.debug(f"Cached results for: {query[:50]}")