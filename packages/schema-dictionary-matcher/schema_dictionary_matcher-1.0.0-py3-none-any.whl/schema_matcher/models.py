"""
Data models for schema matching
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import hashlib
from datetime import datetime


@dataclass
class DictionaryEntry:
    """Dictionary entry from Excel."""
    id: str
    business_name: str
    logical_name: str
    definition: str
    data_type: str
    protection_level: str
    content_hash: str = ""
    domain: str = ""
    sample_values: List[str] = field(default_factory=list)
    is_enum: bool = False
    enum_values: List[str] = field(default_factory=list)
    parent_table: str = ""

    def __post_init__(self):
        if not self.content_hash:
            content = f"{self.business_name}|{self.logical_name}|{self.definition}|{self.data_type}"
            self.content_hash = hashlib.md5(content.encode()).hexdigest()


@dataclass
class AvroField:
    """Avro schema field."""
    name: str
    avro_type: str
    doc: str
    full_path: str
    parent_path: str
    is_array: bool = False
    is_nested: bool = False
    array_item_type: str = ""
    nested_fields: List['AvroField'] = field(default_factory=list)


@dataclass
class MatchResult:
    """Match result with scoring details."""
    avro_field: AvroField
    matched_entry: DictionaryEntry
    rank: int
    final_confidence: float
    semantic_score: float
    lexical_score: float
    edit_distance_score: float
    type_compatibility_score: float
    colbert_score: Optional[float]
    decision: str
    retrieval_stage: str
    latency_ms: float
    cache_hit: bool = False


@dataclass
class SearchResult:
    """Generic search result."""
    doc_id: str
    score: float
    rank: int
    payload: Optional[Dict[str, Any]] = None


@dataclass
class RerankResult:
    """Reranking result."""
    doc_id: str
    score: float
    rank: int
    original_rank: int = 0


@dataclass
class SyncStats:
    """Statistics from sync operation."""
    total_entries: int
    added: int
    modified: int
    deleted: int
    unchanged: int
    duration_seconds: float

    def summary(self) -> str:
        return (
            f"Sync completed in {self.duration_seconds:.2f}s\n"
            f"  Total: {self.total_entries}\n"
            f"  Added: {self.added}\n"
            f"  Modified: {self.modified}\n"
            f"  Deleted: {self.deleted}\n"
            f"  Unchanged: {self.unchanged}"
        )


class SchemaMatcherError(Exception):
    """Base exception for schema matcher."""
    pass


class EmbeddingError(SchemaMatcherError):
    """Embedding generation error."""
    pass


class VectorSearchError(SchemaMatcherError):
    """Vector search error."""
    pass


class InvalidInputError(SchemaMatcherError):
    """Invalid input error."""
    pass