"""
Qdrant vector database manager
"""

import logging
from typing import List, Optional, Tuple, Dict, Any

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter,
    FieldCondition, MatchValue, ScalarQuantization,
    ScalarQuantizationConfig, ScalarType,
    OptimizersConfigDiff, HnswConfigDiff
)

from .config import AdvancedConfig
from .models import DictionaryEntry, SearchResult, VectorSearchError


class VectorDBManager:
    """
    Qdrant vector database manager with optimizations.

    Features:
    - Scalar quantization (3-5x memory reduction)
    - Optimized HNSW parameters
    - Batch operations
    """

    def __init__(self, config: AdvancedConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.client = QdrantClient(path=config.qdrant_path)
        self.collection_name = config.qdrant_collection

    def create_collection(
            self,
            embedding_dim: int,
            force_recreate: bool = False
    ):
        """Create collection with optimized settings."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if exists:
            if force_recreate:
                self.client.delete_collection(self.collection_name)
                self.logger.info(f"Deleted existing collection: {self.collection_name}")
            else:
                self.logger.info(f"Collection {self.collection_name} already exists")
                return

        # Create collection with optimized settings
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=embedding_dim,
                distance=Distance.COSINE
            ),
            optimizers_config=OptimizersConfigDiff(
                default_segment_number=2,
                indexing_threshold=20000
            ),
            hnsw_config=HnswConfigDiff(
                m=self.config.hnsw_m,
                ef_construct=self.config.hnsw_ef_construct
            ),
            quantization_config=ScalarQuantization(
                scalar=ScalarQuantizationConfig(
                    type=ScalarType.INT8,
                    quantile=0.99,
                    always_ram=True
                )
            ) if self.config.use_scalar_quantization else None
        )

        self.logger.info(f"Created collection: {self.collection_name}")

    def upsert_entries(
            self,
            entries: List[DictionaryEntry],
            embeddings: np.ndarray
    ):
        """Upsert entries to vector database."""
        if len(entries) != len(embeddings):
            raise VectorSearchError(
                f"Entries ({len(entries)}) and embeddings ({len(embeddings)}) length mismatch"
            )

        points = []
        for entry, embedding in zip(entries, embeddings):
            # Create payload
            payload = {
                "id": entry.id,
                "business_name": entry.business_name,
                "logical_name": entry.logical_name,
                "definition": entry.definition,
                "data_type": entry.data_type,
                "protection_level": entry.protection_level,
                "content_hash": entry.content_hash,
                "domain": entry.domain,
                "parent_table": entry.parent_table
            }

            # Create point
            point = PointStruct(
                id=hash(entry.id) % (2 ** 63),  # Ensure positive int64
                vector=embedding.tolist(),
                payload=payload
            )
            points.append(point)

        # Batch upsert
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=self.collection_name,
                points=batch
            )

        self.logger.info(f"Upserted {len(points)} points to {self.collection_name}")

    def search(
            self,
            query_embedding: np.ndarray,
            top_k: int = 10,
            filters: Optional[Dict] = None
    ) -> List[Tuple[str, float, Dict]]:
        """
        Search for similar vectors.

        Args:
            query_embedding: Query vector (should be normalized)
            top_k: Number of results to return
            filters: Optional filters

        Returns:
            List of (id, score, payload) tuples with normalized scores
        """
        try:
            # CRITICAL: Normalize query embedding
            norm = np.linalg.norm(query_embedding)
            if norm > 0:
                query_embedding = query_embedding / norm

            # Use query_points instead of deprecated search
            from qdrant_client.models import FieldCondition, Filter, MatchValue

            # Build filter if provided
            qdrant_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
                if conditions:
                    qdrant_filter = Filter(must=conditions)

            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding.tolist(),
                limit=top_k,
                query_filter=qdrant_filter,
                with_payload=True
            )

            # Convert results and ensure scores are in 0-1 range
            output = []
            for point in results.points:
                # Normalize score to 0-1 range (cosine similarity is typically -1 to 1)
                normalized_score = (point.score + 1.0) / 2.0 if point.score < 1.0 else point.score
                normalized_score = max(0.0, min(1.0, normalized_score))

                output.append((
                    point.id,
                    normalized_score,
                    point.payload
                ))

            return output

        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []

    def get_entry_by_id(self, entry_id: str) -> Optional[Dict]:
        """Get entry by ID."""
        try:
            point_id = hash(entry_id) % (2 ** 63)
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id]
            )
            if result:
                return result[0].payload
            return None
        except Exception as e:
            self.logger.error(f"Failed to retrieve entry {entry_id}: {e}")
            return None