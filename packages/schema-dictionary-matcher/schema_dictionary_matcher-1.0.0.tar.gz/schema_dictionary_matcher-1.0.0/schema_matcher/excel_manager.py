"""
Excel dictionary manager
"""

import logging
from pathlib import Path
from typing import List, Optional
import pandas as pd

from .models import DictionaryEntry


class ExcelDictionaryManager:
    """Manager for loading Excel dictionaries."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def load_excel(
            self,
            excel_path: str,
            sheet_name: str = 0,
            id_col: str = "ID",
            business_name_col: str = "Business Name",
            logical_name_col: str = "Logical Name",
            definition_col: str = "Definition",
            data_type_col: str = "Data Type",
            protection_level_col: str = "Protection Level"
    ) -> List[DictionaryEntry]:
        """
        Load dictionary entries from Excel.

        Args:
            excel_path: Path to Excel file
            sheet_name: Sheet name or index
            *_col: Column names for each field

        Returns:
            List of DictionaryEntry objects
        """
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)

            # Check required columns
            required_cols = [
                id_col, business_name_col, logical_name_col,
                definition_col, data_type_col, protection_level_col
            ]

            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Missing columns: {missing_cols}")

            # Convert to entries
            entries = []
            for _, row in df.iterrows():
                entry = DictionaryEntry(
                    id=str(row[id_col]),
                    business_name=str(row[business_name_col]),
                    logical_name=str(row[logical_name_col]),
                    definition=str(row[definition_col]),
                    data_type=str(row[data_type_col]),
                    protection_level=str(row[protection_level_col])
                )
                entries.append(entry)

            self.logger.info(f"Loaded {len(entries)} entries from {excel_path}")
            return entries

        except Exception as e:
            self.logger.error(f"Failed to load Excel: {e}")
            return []