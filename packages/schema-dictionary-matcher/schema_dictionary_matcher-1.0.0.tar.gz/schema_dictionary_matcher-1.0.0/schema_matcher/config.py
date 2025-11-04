"""
Enhanced Configuration for Advanced Schema Matcher
Based on 2024-2025 research (NeurIPS, EMNLP, ACL, VLDB, SIGIR)
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AdvancedConfig:
    """Configuration for advanced schema matching with 2024-2025 optimizations."""

    # Model settings - WITH FALLBACK
    embedding_model: str = "BAAI/bge-base-en-v1.5"  # CHANGED: Use BGE as default (ModernBERT not widely available yet)
    cross_encoder_model: str = "BAAI/bge-reranker-base"
    colbert_model: str = "answerdotai/answerai-colbert-small-v1"

    # Quantization - ENHANCED with binary option
    use_quantization: bool = True
    quantization_type: str = "int8"  # Options: "int8", "binary", "none"
    use_onnx: bool = False  # Set to True if you have ONNX runtime
    use_binary_quantization: bool = False  # NEW: 24-40x speedup option
    binary_rescore_top_k: int = 40  # NEW: Rescore top-40 with INT8

    # ColBERT reranking - ENHANCED with MaxSim
    use_colbert_reranking: bool = False
    colbert_use_maxsim: bool = True  # NEW: Proper late interaction (set to True when you create colbert_maxsim.py)
    colbert_top_k: int = 30

    # Cross-encoder
    rerank_top_k: int = 10

    # Fusion - CONVEX COMBINATION (2-5% better than RRF)
    fusion_method: str = "convex_combination"
    fusion_alpha: float = 0.65

    # Retrieval parameters
    dense_top_k: int = 100
    sparse_top_k: int = 100
    final_top_k: int = 5

    # Type-aware embeddings - ENHANCED with learned projections
    use_type_aware_embeddings: bool = True
    type_embedding_dim: int = 32
    use_learned_type_projections: bool = False  # NEW: Use contrastive learning (set to True when you train model)
    type_projection_model_path: str = "models/type_projections.pt"

    # Semantic caching - ENHANCED with hierarchical L1+L2+L3
    use_semantic_cache: bool = True
    cache_similarity_threshold: float = 0.90
    cache_max_size: int = 10000
    use_hierarchical_cache: bool = True  # NEW: L1+L2+L3 caching (set to True when you create hierarchical_cache.py)
    l1_cache_size: int = 10000  # NEW: In-memory LRU
    use_redis_cache: bool = False  # NEW: L2 Redis cache (optional)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_ttl_seconds: int = 3600

    # Abbreviation expansion
    use_abbreviation_expansion: bool = True
    abbreviation_dict_path: str = "data/abbreviations.json"

    # Batch processing
    batch_size: int = 32
    sort_by_length: bool = True
    normalize_embeddings: bool = True

    # Vector database - ENHANCED with MMR and incremental updates
    qdrant_path: str = "data/qdrant"
    qdrant_collection: str = "schema_dictionary"
    use_scalar_quantization: bool = True
    hnsw_m: int = 16
    hnsw_ef_construct: int = 128
    hnsw_ef: int = 64
    use_mmr: bool = False  # NEW: Maximum Marginal Relevance for diversity
    mmr_diversity_score: float = 0.3

    # Incremental updates - NEW: BLAKE3 change detection
    use_incremental_updates: bool = True
    use_blake3_hashing: bool = True
    change_detection_storage: str = "./data/change_detection.json"

    # Cache and storage
    cache_dir: str = "data/cache"
    bm25_index_path: str = "data/bm25_index.pkl"

    # Confidence thresholds
    auto_approve_threshold: float = 0.75
    review_threshold: float = 0.60

    # Confidence weights
    semantic_weight: float = 0.70
    lexical_weight: float = 0.20
    edit_distance_weight: float = 0.05
    type_compatibility_weight: float = 0.05

    # Domain fine-tuning - NEW
    use_domain_finetuning: bool = True
    finetuned_model_path: Optional[str] = None
    use_hard_negative_mining: bool = True
    hard_negative_margin: float = 0.2

    # Graph-based refinement - NEW
    use_graph_refinement: bool = True
    graph_similarity_threshold: float = 0.7
    graph_max_neighbors: int = 5

    # Logging
    log_dir: str = "logs"
    log_level: str = "INFO"
    enable_metrics: bool = True
    metrics_log_path: str = "logs/metrics.jsonl"

    # Production settings - NEW
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    enable_rate_limiting: bool = False
    rate_limit_requests_per_second: int = 100