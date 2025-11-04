"""
Confidence scoring with multiple signals
"""

import logging
from typing import Tuple, Dict, Optional
import difflib

from .config import AdvancedConfig
from .models import AvroField, DictionaryEntry


class ConfidenceScorer:
    """
    Multi-signal confidence scorer.

    Combines:
    - Semantic similarity (primary signal)
    - Lexical overlap
    - Edit distance
    - Type compatibility
    - Optional ColBERT score
    """

    def __init__(self, config: AdvancedConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def score(
        self,
        avro_field: AvroField,
        entry: DictionaryEntry,
        semantic_score: float,
        colbert_score: Optional[float] = None
    ) -> Tuple[float, Dict[str, float]]:
        """
        Compute final confidence score with proper normalization.

        Args:
            avro_field: Source Avro field
            entry: Target dictionary entry
            semantic_score: Semantic similarity score (0-1)
            colbert_score: Optional ColBERT score

        Returns:
            Tuple of (final_confidence, component_scores)
        """
        # Compute individual components
        lexical = self._compute_lexical_similarity(avro_field, entry)
        edit_dist = self._compute_edit_distance(avro_field, entry)
        type_compat = self._compute_type_compatibility(avro_field, entry)

        # CRITICAL FIX: Ensure semantic_score is in 0-1 range
        # Cross-encoder can return scores outside this range
        semantic_score = max(0.0, min(1.0, semantic_score))

        # Use ColBERT if available, otherwise use semantic
        if colbert_score is not None:
            # ColBERT scores should already be normalized
            colbert_score = max(0.0, min(1.0, colbert_score))
            effective_semantic = (semantic_score + colbert_score) / 2
        else:
            effective_semantic = semantic_score

        # Ensure all components are in 0-1 range
        effective_semantic = max(0.0, min(1.0, effective_semantic))
        lexical = max(0.0, min(1.0, lexical))
        edit_dist = max(0.0, min(1.0, edit_dist))
        type_compat = max(0.0, min(1.0, type_compat))

        # CRITICAL FIX: Weights must sum to 1.0
        total_weight = (
            self.config.semantic_weight +
            self.config.lexical_weight +
            self.config.edit_distance_weight +
            self.config.type_compatibility_weight
        )

        # Normalize weights to sum to 1.0
        sem_w = self.config.semantic_weight / total_weight
        lex_w = self.config.lexical_weight / total_weight
        edit_w = self.config.edit_distance_weight / total_weight
        type_w = self.config.type_compatibility_weight / total_weight

        # Weighted combination
        final_confidence = (
            effective_semantic * sem_w +
            lexical * lex_w +
            edit_dist * edit_w +
            type_compat * type_w
        )

        # Final clamp to ensure 0-1 range
        final_confidence = max(0.0, min(1.0, final_confidence))

        components = {
            "semantic": effective_semantic,
            "lexical": lexical,
            "edit_distance": edit_dist,
            "type_compatibility": type_compat,
            "colbert": colbert_score
        }

        return final_confidence, components

    def _compute_lexical_similarity(
        self,
        avro_field: AvroField,
        entry: DictionaryEntry
    ) -> float:
        """Compute lexical overlap between field and entry."""
        # Combine field information
        field_tokens = set(self._tokenize(avro_field.name))
        if avro_field.doc:
            field_tokens.update(self._tokenize(avro_field.doc))

        # Combine entry information
        entry_tokens = set(self._tokenize(entry.business_name))
        entry_tokens.update(self._tokenize(entry.logical_name))
        entry_tokens.update(self._tokenize(entry.definition))

        # Compute Jaccard similarity
        if not field_tokens or not entry_tokens:
            return 0.0

        intersection = len(field_tokens & entry_tokens)
        union = len(field_tokens | entry_tokens)

        return intersection / union if union > 0 else 0.0

    def _compute_edit_distance(
        self,
        avro_field: AvroField,
        entry: DictionaryEntry
    ) -> float:
        """Compute normalized edit distance score."""
        # Use field name and entry logical name for edit distance
        field_name = avro_field.name.lower()
        entry_name = entry.logical_name.lower()

        # Use difflib for sequence matching
        ratio = difflib.SequenceMatcher(None, field_name, entry_name).ratio()

        return ratio

    def _compute_type_compatibility(
        self,
        avro_field: AvroField,
        entry: DictionaryEntry
    ) -> float:
        """Compute type compatibility score."""
        # Normalize types
        avro_type = self._normalize_type(avro_field.avro_type)
        entry_type = self._normalize_type(entry.data_type)

        # Exact match
        if avro_type == entry_type:
            return 1.0

        # Compatible types
        compatible_groups = [
            {"string", "text", "varchar"},
            {"int", "integer", "long", "bigint"},
            {"float", "double", "decimal", "numeric"},
            {"date", "timestamp", "datetime"},
            {"boolean", "bool"},
        ]

        for group in compatible_groups:
            if avro_type in group and entry_type in group:
                return 0.8

        # Numeric types are somewhat compatible
        numeric_types = {"int", "integer", "long", "bigint", "float", "double", "decimal", "numeric"}
        if avro_type in numeric_types and entry_type in numeric_types:
            return 0.6

        # No compatibility
        return 0.0

    def _normalize_type(self, data_type: str) -> str:
        """Normalize data type string."""
        data_type = data_type.lower()

        # Map common variations
        type_map = {
            "varchar": "string",
            "char": "string",
            "text": "string",
            "bigint": "long",
            "int": "integer",
            "numeric": "decimal",
            "datetime": "timestamp",
            "bool": "boolean"
        }

        for key, value in type_map.items():
            if key in data_type:
                return value

        return data_type

    def _tokenize(self, text: str) -> list:
        """Tokenize text into words."""
        if not text:
            return []

        # Convert to lowercase and split on common delimiters
        text = text.lower()

        # Replace common separators with spaces
        for sep in ['_', '-', '.', '/', '\\']:
            text = text.replace(sep, ' ')

        # Split and filter
        tokens = [t.strip() for t in text.split() if len(t.strip()) > 1]

        return tokens

    def get_decision(self, confidence: float) -> str:
        """
        Determine decision based on confidence score.

        Args:
            confidence: Confidence score (0-1)

        Returns:
            Decision string: AUTO_APPROVE, REVIEW, or REJECT
        """
        if confidence >= self.config.auto_approve_threshold:
            return "AUTO_APPROVE"
        elif confidence >= self.config.review_threshold:
            return "REVIEW"
        else:
            return "REJECT"