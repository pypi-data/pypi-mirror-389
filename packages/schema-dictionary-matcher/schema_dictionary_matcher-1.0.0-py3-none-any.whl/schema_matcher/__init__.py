"""
Schema Dictionary Matcher - Production-ready semantic schema matching

Features:
- Sub-100ms P95 latency
- 60%+ auto-approval rate
- 100% offline operation (no HuggingFace access required)
- REST API with Swagger UI
- Docker & Kubernetes ready
"""

__version__ = "1.0.0"
__author__ = "Pierce Lonergan"
__email__ = "lonerganpierce@gmail.com"

# Import from modules in this package
from .schema_matcher import AdvancedSchemaMatcher
from .config_production import ProductionConfig
from .config import AdvancedConfig
from .models import (
    DictionaryEntry,
    AvroField,
    MatchResult,
    SyncStats,
)

__all__ = [
    "AdvancedSchemaMatcher",
    "ProductionConfig",
    "AdvancedConfig",
    "DictionaryEntry",
    "AvroField",
    "MatchResult",
    "SyncStats",
]