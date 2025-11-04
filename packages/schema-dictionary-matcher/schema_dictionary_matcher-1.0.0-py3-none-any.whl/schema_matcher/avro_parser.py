"""
Avro schema parser
"""

import json
import logging
from typing import List
from pathlib import Path

from .models import AvroField


class AvroSchemaParser:
    """Parser for Avro schema files."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse_schema(self, schema_path: str) -> List[AvroField]:
        """
        Parse Avro schema file.

        Args:
            schema_path: Path to .avsc file

        Returns:
            List of AvroField objects
        """
        try:
            with open(schema_path, 'r') as f:
                schema = json.load(f)

            fields = []
            self._extract_fields(schema, "", fields)

            self.logger.info(f"Extracted {len(fields)} fields from {schema_path}")
            return fields

        except Exception as e:
            self.logger.error(f"Failed to parse schema: {e}")
            return []

    def _extract_fields(
            self,
            schema: dict,
            parent_path: str,
            fields: List[AvroField]
    ):
        """Recursively extract fields from schema."""
        if not isinstance(schema, dict):
            return

        # Handle record type
        if schema.get("type") == "record":
            record_name = schema.get("name", "")
            record_fields = schema.get("fields", [])

            for field in record_fields:
                field_name = field.get("name", "")
                field_type = self._get_field_type(field.get("type"))
                field_doc = field.get("doc", "")

                full_path = f"{parent_path}.{field_name}" if parent_path else field_name

                avro_field = AvroField(
                    name=field_name,
                    avro_type=field_type,
                    doc=field_doc,
                    full_path=full_path,
                    parent_path=parent_path,
                    is_array="array" in str(field.get("type")),
                    is_nested="record" in str(field.get("type"))
                )

                fields.append(avro_field)

                # Recursively process nested records
                if isinstance(field.get("type"), dict):
                    self._extract_fields(field["type"], full_path, fields)
                elif isinstance(field.get("type"), list):
                    for type_option in field["type"]:
                        if isinstance(type_option, dict):
                            self._extract_fields(type_option, full_path, fields)

    def _get_field_type(self, type_def) -> str:
        """Extract type string from type definition."""
        if isinstance(type_def, str):
            return type_def
        elif isinstance(type_def, dict):
            return type_def.get("type", "unknown")
        elif isinstance(type_def, list):
            # Union type - get non-null type
            non_null_types = [t for t in type_def if t != "null"]
            if non_null_types:
                return self._get_field_type(non_null_types[0])
            return "null"
        return "unknown"