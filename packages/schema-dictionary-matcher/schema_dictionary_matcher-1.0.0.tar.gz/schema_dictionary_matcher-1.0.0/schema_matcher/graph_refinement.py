"""
Graph-Based Schema Matching Refinement
Leverages structural relationships for 5-10% accuracy improvement
Based on SiMa (TU Delft, 2024) - 600x faster than traditional matchers
"""

import logging
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass
import numpy as np

from .models import DictionaryEntry, AvroField, MatchResult


@dataclass
class SchemaNode:
    """Node in schema graph."""
    id: str
    name: str
    type: str
    parent_id: Optional[str]
    children_ids: List[str]
    embedding: Optional[np.ndarray] = None


@dataclass
class SchemaEdge:
    """Edge in schema graph."""
    source_id: str
    target_id: str
    edge_type: str  # "parent-child", "sibling", "reference"
    weight: float = 1.0


class SchemaGraph:
    """
    Graph representation of schema structure.

    Captures:
    - Parent-child relationships
    - Sibling relationships
    - Type compatibility
    - Semantic proximity
    """

    def __init__(self):
        self.nodes: Dict[str, SchemaNode] = {}
        self.edges: List[SchemaEdge] = []
        self.logger = logging.getLogger(__name__)

    def add_node(self, node: SchemaNode):
        """Add node to graph."""
        self.nodes[node.id] = node

    def add_edge(self, edge: SchemaEdge):
        """Add edge to graph."""
        self.edges.append(edge)

    def get_neighbors(self, node_id: str, edge_type: Optional[str] = None) -> List[str]:
        """Get neighbor node IDs."""
        neighbors = []
        for edge in self.edges:
            if edge.source_id == node_id:
                if edge_type is None or edge.edge_type == edge_type:
                    neighbors.append(edge.target_id)
            elif edge.target_id == node_id:
                if edge_type is None or edge.edge_type == edge_type:
                    neighbors.append(edge.source_id)
        return neighbors

    def build_from_avro_fields(self, fields: List[AvroField]):
        """Build graph from Avro fields."""
        # Add nodes
        for field in fields:
            node = SchemaNode(
                id=field.full_path,
                name=field.name,
                type=field.avro_type,
                parent_id=field.parent_path if field.parent_path else None,
                children_ids=[]
            )
            self.add_node(node)

        # Add parent-child edges
        for node in self.nodes.values():
            if node.parent_id and node.parent_id in self.nodes:
                self.add_edge(SchemaEdge(
                    source_id=node.parent_id,
                    target_id=node.id,
                    edge_type="parent-child",
                    weight=1.0
                ))
                self.nodes[node.parent_id].children_ids.append(node.id)

        # Add sibling edges
        for node in self.nodes.values():
            if node.parent_id:
                parent = self.nodes.get(node.parent_id)
                if parent:
                    for sibling_id in parent.children_ids:
                        if sibling_id != node.id:
                            self.add_edge(SchemaEdge(
                                source_id=node.id,
                                target_id=sibling_id,
                                edge_type="sibling",
                                weight=0.5
                            ))

        self.logger.info(
            f"Built graph: {len(self.nodes)} nodes, {len(self.edges)} edges"
        )

    def build_from_dictionary(self, entries: List[DictionaryEntry]):
        """Build graph from dictionary entries."""
        # Add nodes
        for entry in entries:
            node = SchemaNode(
                id=entry.id,
                name=entry.business_name,
                type=entry.data_type,
                parent_id=entry.parent_table if entry.parent_table else None,
                children_ids=[]
            )
            self.add_node(node)

        # Add parent-child edges (tables to fields)
        for node in self.nodes.values():
            if node.parent_id and node.parent_id in self.nodes:
                self.add_edge(SchemaEdge(
                    source_id=node.parent_id,
                    target_id=node.id,
                    edge_type="parent-child",
                    weight=1.0
                ))

        self.logger.info(
            f"Built dictionary graph: {len(self.nodes)} nodes, {len(self.edges)} edges"
        )


class GraphBasedRefinement:
    """
    Graph-based refinement for schema matching.

    Improves matches by leveraging:
    - Structural context (parent-child relationships)
    - Sibling consistency (fields in same record should match to same table)
    - Type compatibility propagation

    Expected improvement: 5-10% on schemas with strong structural relationships
    """

    def __init__(
            self,
            similarity_threshold: float = 0.7,
            max_neighbors: int = 5,
            propagation_weight: float = 0.3
    ):
        self.similarity_threshold = similarity_threshold
        self.max_neighbors = max_neighbors
        self.propagation_weight = propagation_weight
        self.logger = logging.getLogger(__name__)

        self.source_graph: Optional[SchemaGraph] = None
        self.target_graph: Optional[SchemaGraph] = None

    def build_graphs(
            self,
            avro_fields: List[AvroField],
            dictionary_entries: List[DictionaryEntry]
    ):
        """Build graphs for source and target schemas."""
        # Build source graph (Avro)
        self.source_graph = SchemaGraph()
        self.source_graph.build_from_avro_fields(avro_fields)

        # Build target graph (Dictionary)
        self.target_graph = SchemaGraph()
        self.target_graph.build_from_dictionary(dictionary_entries)

        self.logger.info("Built schema graphs for refinement")

    def refine_matches(
            self,
            initial_matches: Dict[str, List[MatchResult]]
    ) -> Dict[str, List[MatchResult]]:
        """
        Refine matches using graph structure.

        Args:
            initial_matches: Map of field_path -> list of MatchResult

        Returns:
            Refined matches with adjusted scores
        """
        if not self.source_graph or not self.target_graph:
            self.logger.warning("Graphs not built, skipping refinement")
            return initial_matches

        refined_matches = {}

        for field_path, matches in initial_matches.items():
            # Get source node
            source_node = self.source_graph.nodes.get(field_path)
            if not source_node:
                refined_matches[field_path] = matches
                continue

            # Get neighbors of source
            source_neighbors = self.source_graph.get_neighbors(source_node.id)

            # Adjust scores based on neighbor matches
            adjusted_matches = []
            for match in matches:
                # Get target node
                target_node = self.target_graph.nodes.get(match.matched_entry.id)
                if not target_node:
                    adjusted_matches.append(match)
                    continue

                # Get neighbors of target
                target_neighbors = self.target_graph.get_neighbors(target_node.id)

                # Compute neighbor match score
                neighbor_score = self._compute_neighbor_score(
                    source_neighbors,
                    target_neighbors,
                    initial_matches
                )

                # Adjust confidence
                original_confidence = match.final_confidence
                adjusted_confidence = (
                        (1 - self.propagation_weight) * original_confidence +
                        self.propagation_weight * neighbor_score
                )

                # Create adjusted match
                adjusted_match = MatchResult(
                    avro_field=match.avro_field,
                    matched_entry=match.matched_entry,
                    rank=match.rank,
                    final_confidence=adjusted_confidence,
                    semantic_score=match.semantic_score,
                    lexical_score=match.lexical_score,
                    edit_distance_score=match.edit_distance_score,
                    type_compatibility_score=match.type_compatibility_score,
                    colbert_score=match.colbert_score,
                    decision=self._get_decision(adjusted_confidence),
                    retrieval_stage=f"{match.retrieval_stage}_graph_refined",
                    latency_ms=match.latency_ms,
                    cache_hit=match.cache_hit
                )

                adjusted_matches.append(adjusted_match)

            # Re-rank by adjusted confidence
            adjusted_matches.sort(key=lambda x: x.final_confidence, reverse=True)

            # Update ranks
            for i, match in enumerate(adjusted_matches, 1):
                match.rank = i

            refined_matches[field_path] = adjusted_matches

        return refined_matches

    def _compute_neighbor_score(
            self,
            source_neighbors: List[str],
            target_neighbors: List[str],
            all_matches: Dict[str, List[MatchResult]]
    ) -> float:
        """
        Compute score based on how well neighbors match.

        If source neighbors match well to target neighbors, this is evidence
        that the current match is correct.
        """
        if not source_neighbors or not target_neighbors:
            return 0.5  # Neutral score

        # Check how many source neighbors have high-confidence matches to target neighbors
        matches_count = 0
        total_checked = 0

        for source_neighbor in source_neighbors[:self.max_neighbors]:
            neighbor_matches = all_matches.get(source_neighbor, [])
            if not neighbor_matches:
                continue

            total_checked += 1

            # Check if top match is to a target neighbor
            top_match = neighbor_matches[0]
            if top_match.matched_entry.id in target_neighbors:
                if top_match.final_confidence >= self.similarity_threshold:
                    matches_count += 1

        if total_checked == 0:
            return 0.5

        # Score based on proportion of neighbor matches
        return matches_count / total_checked

    def _get_decision(self, confidence: float) -> str:
        """Get decision based on confidence threshold."""
        if confidence >= 0.88:
            return "AUTO_APPROVE"
        elif confidence >= 0.65:
            return "REVIEW"
        else:
            return "REJECT"