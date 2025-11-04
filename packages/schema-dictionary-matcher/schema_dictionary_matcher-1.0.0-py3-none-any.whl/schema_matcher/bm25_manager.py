"""
Enhanced BM25 Manager with incremental update support
"""

import logging
import pickle
from pathlib import Path
from typing import List, Tuple

from rank_bm25 import BM25Okapi

from .config import AdvancedConfig
from .models import DictionaryEntry


class BM25Manager:
    """BM25 sparse retrieval with incremental updates."""

    def __init__(self, config: AdvancedConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.index_path = Path(config.bm25_index_path)
        self.bm25 = None
        self.doc_ids = []
        self.corpus = []
        self.doc_id_to_idx = {}

        # Try to load existing index
        self._load_index()

    def build_index(self, entries: List[DictionaryEntry]):
        """Build BM25 index from entries."""
        self.doc_ids = [entry.id for entry in entries]

        # Tokenize corpus
        self.corpus = []
        for entry in entries:
            text = f"{entry.business_name} {entry.logical_name} {entry.definition}"
            tokens = text.lower().split()
            self.corpus.append(tokens)

        # Build ID to index mapping
        self.doc_id_to_idx = {doc_id: idx for idx, doc_id in enumerate(self.doc_ids)}

        # Build BM25 index
        self.bm25 = BM25Okapi(self.corpus)

        self.logger.info(f"Built BM25 index with {len(self.corpus)} documents")

    def update_index(self, entries: List[DictionaryEntry], deleted_ids: List[str]):
        """
        Update BM25 index incrementally.

        Args:
            entries: Entries to add/update
            deleted_ids: IDs to remove
        """
        # Remove deleted entries
        if deleted_ids:
            indices_to_remove = sorted(
                [self.doc_id_to_idx[id] for id in deleted_ids if id in self.doc_id_to_idx],
                reverse=True
            )

            for idx in indices_to_remove:
                del self.doc_ids[idx]
                del self.corpus[idx]

            # Rebuild ID mapping
            self.doc_id_to_idx = {doc_id: idx for idx, doc_id in enumerate(self.doc_ids)}

        # Add/update entries
        for entry in entries:
            text = f"{entry.business_name} {entry.logical_name} {entry.definition}"
            tokens = text.lower().split()

            if entry.id in self.doc_id_to_idx:
                # Update existing
                idx = self.doc_id_to_idx[entry.id]
                self.corpus[idx] = tokens
            else:
                # Add new
                self.doc_ids.append(entry.id)
                self.corpus.append(tokens)
                self.doc_id_to_idx[entry.id] = len(self.doc_ids) - 1

        # Rebuild BM25 index
        self.bm25 = BM25Okapi(self.corpus)

        self.logger.info(
            f"Updated BM25 index: added/updated {len(entries)}, "
            f"deleted {len(deleted_ids)}, total {len(self.corpus)}"
        )

    def remove_entries(self, doc_ids: List[str]):
        """Remove entries from index."""
        self.update_index([], doc_ids)

    def save_index(self):
        """Save BM25 index to disk."""
        try:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'bm25': self.bm25,
                'doc_ids': self.doc_ids,
                'corpus': self.corpus,
                'doc_id_to_idx': self.doc_id_to_idx
            }

            with open(self.index_path, 'wb') as f:
                pickle.dump(data, f)

            self.logger.info(f"Saved BM25 index to {self.index_path}")
        except Exception as e:
            self.logger.error(f"Failed to save BM25 index: {e}")

    def _load_index(self):
        """Load BM25 index from disk."""
        if self.index_path.exists():
            try:
                with open(self.index_path, 'rb') as f:
                    data = pickle.load(f)

                self.bm25 = data['bm25']
                self.doc_ids = data['doc_ids']
                self.corpus = data['corpus']
                self.doc_id_to_idx = data.get('doc_id_to_idx', {})

                # Rebuild mapping if not present
                if not self.doc_id_to_idx:
                    self.doc_id_to_idx = {doc_id: idx for idx, doc_id in enumerate(self.doc_ids)}

                self.logger.info(f"Loaded BM25 index from {self.index_path}")
            except Exception as e:
                self.logger.warning(f"Failed to load BM25 index: {e}")

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Search using BM25."""
        if self.bm25 is None:
            self.logger.warning("BM25 index not built")
            return []

        query_tokens = query.lower().split()
        scores = self.bm25.get_scores(query_tokens)
        top_indices = scores.argsort()[-top_k:][::-1]

        results = [
            (self.doc_ids[i], float(scores[i]))
            for i in top_indices
        ]

        return results