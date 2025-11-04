"""
Production FastAPI Server for Advanced Schema Matcher
"""

# Allow direct execution
import sys
from pathlib import Path
if __name__ == "__main__" or not __package__:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
import time
import logging
from datetime import datetime
import json
import tempfile
from starlette.responses import Response
import traceback

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DATA_DIR = PROJECT_ROOT / "data"

# Use absolute imports
from schema_matcher.config_production import ProductionConfig
from schema_matcher.schema_matcher import AdvancedSchemaMatcher

# ==================== SETUP LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# ==================== METRICS (Lazy loading to avoid duplicates) ====================

_metrics_initialized = False
REQUEST_COUNT = None
REQUEST_LATENCY = None
ACTIVE_REQUESTS = None
CACHE_HITS = None
AUTO_APPROVALS = None

def init_metrics():
    """Initialize Prometheus metrics once."""
    global _metrics_initialized, REQUEST_COUNT, REQUEST_LATENCY, ACTIVE_REQUESTS, CACHE_HITS, AUTO_APPROVALS

    if _metrics_initialized:
        return

    from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

    # Create a custom registry to avoid conflicts
    custom_registry = CollectorRegistry()

    REQUEST_COUNT = Counter(
        'schema_matcher_requests_total',
        'Total number of requests',
        ['endpoint', 'status'],
        registry=custom_registry
    )

    REQUEST_LATENCY = Histogram(
        'schema_matcher_request_duration_seconds',
        'Request latency in seconds',
        ['endpoint'],
        registry=custom_registry
    )

    ACTIVE_REQUESTS = Gauge(
        'schema_matcher_active_requests',
        'Number of active requests',
        registry=custom_registry
    )

    CACHE_HITS = Counter(
        'schema_matcher_cache_hits_total',
        'Total cache hits',
        registry=custom_registry
    )

    AUTO_APPROVALS = Counter(
        'schema_matcher_auto_approvals_total',
        'Total auto-approvals',
        registry=custom_registry
    )

    _metrics_initialized = True
    return custom_registry


# ==================== MODELS ====================

class AvroSchemaRequest(BaseModel):
    """Request model for schema matching."""
    avro_schema: Dict[str, Any] = Field(..., description="Avro schema as JSON object", alias="schema")
    return_top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of top matches to return")

    @field_validator('avro_schema')
    @classmethod
    def validate_schema(cls, v):
        """Validate Avro schema structure."""
        if not isinstance(v, dict):
            raise ValueError("Schema must be a JSON object")
        if 'type' not in v:
            raise ValueError("Schema must have 'type' field")
        if 'fields' not in v and v.get('type') != 'record':
            raise ValueError("Record schema must have 'fields'")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "schema": {
                    "type": "record",
                    "name": "Customer",
                    "fields": [
                        {
                            "name": "customer_email",
                            "type": "string",
                            "doc": "Customer email address"
                        },
                        {
                            "name": "transaction_amount",
                            "type": "double",
                            "doc": "Transaction amount in USD"
                        }
                    ]
                },
                "return_top_k": 5
            }
        }
    }


class MatchResult(BaseModel):
    """Single match result."""
    rank: int
    field_path: str
    matched_id: str
    matched_name: str
    matched_logical_name: str
    matched_definition: str  # ← NEW
    matched_data_type: str  # ← NEW
    matched_protection_level: Optional[str]  # ← NEW
    confidence: float
    decision: str
    semantic_score: float
    lexical_score: float
    type_compatibility: float
    latency_ms: float
    cache_hit: bool


class MatchResponse(BaseModel):
    """Response model for schema matching."""
    success: bool
    request_id: str
    timestamp: str
    total_fields: int
    matched_fields: int
    total_latency_ms: float
    avg_latency_ms: float
    matches: List[MatchResult]
    metadata: Dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    uptime_seconds: float
    models_loaded: bool
    cache_enabled: bool
    total_requests: int


class DictionarySyncResponse(BaseModel):
    """Response for dictionary sync."""
    success: bool
    message: str
    filename: str
    total_entries: int
    added: int
    modified: int
    deleted: int
    unchanged: int


# ==================== STATE ====================

class AppState:
    """Application state management."""
    def __init__(self):
        self.matcher = None
        self.start_time = time.time()
        self.request_count = 0
        self.config = None
        self.logger = logging.getLogger(__name__)
        self.metrics_registry = None

state = AppState()


# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    state.logger.info("Starting Advanced Schema Matcher API...")

    try:
        # Initialize metrics
        state.metrics_registry = init_metrics()
        state.logger.info("✅ Metrics initialized")

        # Load configuration
        state.config = ProductionConfig()
        state.config.log_level = "WARNING"

        # Initialize matcher
        from schema_matcher import AdvancedSchemaMatcher
        state.matcher = AdvancedSchemaMatcher(state.config)

        # AUTO-LOAD DICTIONARY ON STARTUP
        dictionary_path = (DATA_DIR / "sample_dictionary.xlsx")
        if dictionary_path.exists():
            state.logger.info(f"Loading dictionary from {dictionary_path}...")
            stats = state.matcher.sync_excel_to_vector_db(str(dictionary_path), force_rebuild=True)
            state.logger.info(f"✅ Dictionary loaded: {stats.total_entries} entries")
        else:
            state.logger.warning(f"⚠️  Dictionary not found at {dictionary_path}")

        # Warm up models
        state.logger.info("Warming up models...")
        warmup_schema = {
            "type": "record",
            "name": "Warmup",
            "fields": [{"name": "test", "type": "string"}]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.avsc', delete=False) as f:
            json.dump(warmup_schema, f)
            warmup_path = f.name

        state.matcher.match_avro_schema(warmup_path)
        Path(warmup_path).unlink()

        state.logger.info("✅ API ready! Models loaded and warmed up.")

    except Exception as e:
        state.logger.error(f"Failed to initialize: {e}")
        state.logger.error(traceback.format_exc())
        raise

    yield

    # Shutdown
    state.logger.info("Shutting down Advanced Schema Matcher API...")


# ==================== APPLICATION ====================

app = FastAPI(
    title="Advanced Schema Matcher API",
    description="Production API for semantic schema matching with sub-100ms latency",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== DEPENDENCIES ====================

def get_matcher():
    """Dependency to get matcher instance."""
    if state.matcher is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Matcher not initialized"
        )
    return state.matcher


# ==================== ENDPOINTS ====================

@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirect."""
    return {"message": "Advanced Schema Matcher API", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Kubernetes probes."""
    if REQUEST_COUNT:
        REQUEST_COUNT.labels(endpoint='/health', status='success').inc()

    return HealthResponse(
        status="healthy" if state.matcher else "initializing",
        version="1.0.0",
        uptime_seconds=time.time() - state.start_time,
        models_loaded=state.matcher is not None,
        cache_enabled=state.config.use_hierarchical_cache if state.config else False,
        total_requests=state.request_count
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    if state.metrics_registry:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return Response(generate_latest(state.metrics_registry), media_type=CONTENT_TYPE_LATEST)
    return {"error": "Metrics not initialized"}


@app.post("/match", response_model=MatchResponse)
async def match_schema(
        request: AvroSchemaRequest,
        background_tasks: BackgroundTasks,
        matcher=Depends(get_matcher)
):
    """
    Match Avro schema fields to data dictionary entries.

    Returns top-K matches for each field with confidence scores.
    """
    request_id = f"req_{int(time.time() * 1000)}"
    start_time = time.time()

    if ACTIVE_REQUESTS:
        ACTIVE_REQUESTS.inc()
    state.request_count += 1

    try:
        # Create temporary schema file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.avsc', delete=False) as f:
            json.dump(request.avro_schema, f)
            schema_path = f.name

        # Perform matching
        if REQUEST_LATENCY:
            with REQUEST_LATENCY.labels(endpoint='/match').time():
                results = matcher.match_avro_schema(schema_path)
        else:
            results = matcher.match_avro_schema(schema_path)

        # Clean up temp file
        Path(schema_path).unlink()

        # Process results
        matches = []
        cache_hits = 0
        auto_approvals = 0

        for result in results:
            if result.cache_hit:
                cache_hits += 1
                if CACHE_HITS:
                    CACHE_HITS.inc()

            if result.decision == "AUTO_APPROVE":
                auto_approvals += 1
                if AUTO_APPROVALS:
                    AUTO_APPROVALS.inc()

            # Include all dictionary entry fields in response
            matches.append(MatchResult(
                rank=result.rank,
                field_path=result.avro_field.full_path,
                matched_id=str(result.matched_entry.id),
                matched_name=result.matched_entry.business_name,
                matched_logical_name=result.matched_entry.logical_name,
                matched_definition=result.matched_entry.definition,  # ← NEW
                matched_data_type=result.matched_entry.data_type,  # ← NEW
                matched_protection_level=result.matched_entry.protection_level,  # ← NEW
                confidence=result.final_confidence,
                decision=result.decision,
                semantic_score=result.semantic_score,
                lexical_score=result.lexical_score,
                type_compatibility=result.type_compatibility_score,
                latency_ms=result.latency_ms,
                cache_hit=result.cache_hit
            ))

        # Calculate metrics
        total_latency = (time.time() - start_time) * 1000
        unique_fields = len(set(m.field_path for m in matches))
        avg_latency = sum(m.latency_ms for m in matches) / len(matches) if matches else 0

        if REQUEST_COUNT:
            REQUEST_COUNT.labels(endpoint='/match', status='success').inc()

        return MatchResponse(
            success=True,
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
            total_fields=unique_fields,
            matched_fields=len(matches),
            total_latency_ms=total_latency,
            avg_latency_ms=avg_latency,
            matches=matches[:request.return_top_k * unique_fields],
            metadata={
                "cache_hit_rate": cache_hits / len(matches) if matches else 0,
                "auto_approval_rate": auto_approvals / unique_fields if unique_fields > 0 else 0,
                "config": {
                    "embedding_model": state.config.embedding_model,
                    "use_colbert": state.config.use_colbert_reranking,
                    "cache_enabled": state.config.use_hierarchical_cache
                }
            }
        )

    except Exception as e:
        if REQUEST_COUNT:
            REQUEST_COUNT.labels(endpoint='/match', status='error').inc()
        state.logger.error(f"Match failed: {e}")
        state.logger.error(traceback.format_exc())

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Matching failed: {str(e)}"
        )

    finally:
        if ACTIVE_REQUESTS:
            ACTIVE_REQUESTS.dec()


@app.post("/sync-dictionary", response_model=DictionarySyncResponse)
async def sync_dictionary(
        file: UploadFile = File(..., description="Excel dictionary file (.xlsx or .xls)"),
        force_rebuild: bool = False,
        matcher=Depends(get_matcher)
):
    """
    Upload and sync data dictionary from Excel file.

    Drag and drop your Excel file here!

    **Excel Format Required:**
    - Column: ID (required)
    - Column: Business Name (required)
    - Column: Logical Name (required)
    - Column: Definition (required)
    - Column: Data Type (required)
    - Column: Protection Level (optional)
    """
    try:
        # Validate file extension
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be Excel format (.xlsx or .xls)"
            )

        state.logger.info(f"Received dictionary upload: {file.filename}")

        # Save uploaded file to temporary location
        temp_dir = Path("data/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_file_path = temp_dir / f"upload_{int(time.time())}_{file.filename}"

        # Write uploaded file
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        state.logger.info(f"Saved upload to: {temp_file_path}")

        # Perform sync
        stats = matcher.sync_excel_to_vector_db(
            str(temp_file_path),
            force_rebuild=force_rebuild
        )

        # Clean up temp file
        temp_file_path.unlink()

        state.logger.info(f"✅ Dictionary synced: {stats.total_entries} entries")

        return DictionarySyncResponse(
            success=True,
            message=f"Dictionary synced successfully from {file.filename}",
            filename=file.filename,
            total_entries=stats.total_entries,
            added=stats.added,
            modified=stats.modified,
            deleted=stats.deleted,
            unchanged=stats.unchanged
        )

    except HTTPException:
        raise
    except Exception as e:
        state.logger.error(f"Sync failed: {e}")
        state.logger.error(traceback.format_exc())

        # Clean up temp file on error
        if 'temp_file_path' in locals() and temp_file_path.exists():
            temp_file_path.unlink()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@app.get("/dictionary-format")
async def get_dictionary_format():
    """
    Get the required Excel format for dictionary upload.

    Returns example structure and column definitions.
    """
    return {
        "required_columns": {
            "ID": {
                "description": "Unique identifier for the dictionary entry",
                "example": "field_001",
                "required": True
            },
            "Business Name": {
                "description": "Human-readable name of the field",
                "example": "Customer Email Address",
                "required": True
            },
            "Logical Name": {
                "description": "Technical/logical name of the field",
                "example": "cust_email",
                "required": True
            },
            "Definition": {
                "description": "Detailed description of what the field contains",
                "example": "Email address for customer communication",
                "required": True
            },
            "Data Type": {
                "description": "Data type of the field",
                "example": "string",
                "required": True,
                "common_values": ["string", "integer", "long", "double", "boolean", "date", "timestamp"]
            },
            "Protection Level": {
                "description": "Data sensitivity classification",
                "example": "PII",
                "required": False,
                "common_values": ["PII", "Internal", "Public", "Confidential"]
            }
        },
        "example_rows": [
            {
                "ID": "field_001",
                "Business Name": "Customer Email Address",
                "Logical Name": "cust_email",
                "Definition": "Email address for customer",
                "Data Type": "string",
                "Protection Level": "PII"
            },
            {
                "ID": "field_002",
                "Business Name": "Transaction Amount",
                "Logical Name": "txn_amt",
                "Definition": "Amount of transaction in USD",
                "Data Type": "double",
                "Protection Level": "Internal"
            }
        ],
        "download_template": "/dictionary-template"
    }


@app.get("/dictionary-template")
async def download_dictionary_template():
    """
    Download an Excel template for dictionary upload.
    """
    import pandas as pd
    from io import BytesIO

    # Create sample template
    template_data = {
        "ID": ["field_001", "field_002", "field_003"],
        "Business Name": ["Customer Email Address", "Transaction Amount", "Account Balance"],
        "Logical Name": ["cust_email", "txn_amt", "acct_bal"],
        "Definition": [
            "Email address for customer communication",
            "Transaction amount in USD",
            "Current account balance"
        ],
        "Data Type": ["string", "double", "double"],
        "Protection Level": ["PII", "Internal", "Internal"]
    }

    df = pd.DataFrame(template_data)

    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Dictionary')

        # Auto-adjust column widths
        worksheet = writer.sheets['Dictionary']
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(col)
            ) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = max_length

    output.seek(0)

    from starlette.responses import StreamingResponse

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=dictionary_template.xlsx"
        }
    )


@app.get("/dictionary-status")
async def get_dictionary_status(matcher=Depends(get_matcher)):
    """Check if dictionary is loaded and get statistics."""
    try:
        # Try to get collection info from vector DB
        collection_info = matcher.vector_db.client.get_collection(
            collection_name=matcher.vector_db.collection_name
        )

        return {
            "loaded": True,
            "collection_name": matcher.vector_db.collection_name,
            "total_entries": collection_info.points_count if hasattr(collection_info, 'points_count') else 0,
            "vector_dimension": matcher.embedding_gen.embedding_dim,
            "cache_enabled": matcher.config.use_hierarchical_cache,
            "ready_for_matching": True
        }
    except Exception as e:
        return {
            "loaded": False,
            "error": str(e),
            "ready_for_matching": False,
            "message": "Please upload a dictionary using /sync-dictionary"
        }

@app.get("/stats")
async def get_stats():
    """Get current statistics."""
    if state.matcher and hasattr(state.matcher, 'cache') and state.matcher.cache:
        cache_stats = state.matcher.cache.get_stats()
    else:
        cache_stats = None

    return {
        "uptime_seconds": time.time() - state.start_time,
        "total_requests": state.request_count,
        "cache_stats": {
            "hit_rate": cache_stats.hit_rate if cache_stats else 0,
            "l1_hits": cache_stats.l1_hits if cache_stats else 0,
            "total_queries": cache_stats.total_queries if cache_stats else 0
        } if cache_stats else None
    }


# ==================== ERROR HANDLERS ====================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    state.logger.error(f"Unhandled exception: {exc}")
    state.logger.error(traceback.format_exc())

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Add these models after the existing ones:

class AbbreviationEntry(BaseModel):
    """Single abbreviation entry."""
    abbreviation: str = Field(..., description="The abbreviation (e.g., 'cust')")
    expansion: str = Field(..., description="The full form (e.g., 'customer')")


class AbbreviationsResponse(BaseModel):
    """Response with all abbreviations."""
    total: int
    abbreviations: Dict[str, str]


class AbbreviationUpdateRequest(BaseModel):
    """Request to add/update abbreviations."""
    abbreviations: Dict[str, str] = Field(..., description="Dictionary of abbreviation: expansion pairs")

    model_config = {
        "json_schema_extra": {
            "example": {
                "abbreviations": {
                    "cust": "customer",
                    "txn": "transaction",
                    "acct": "account",
                    "addr": "address"
                }
            }
        }
    }


# Add these endpoints:

@app.get("/abbreviations", response_model=AbbreviationsResponse)
async def get_abbreviations(matcher=Depends(get_matcher)):
    """
    Get all currently loaded abbreviations.

    Returns a dictionary of abbreviation → expansion mappings.
    """
    try:
        abbreviations = matcher.abbreviation_expander.abbreviations

        return AbbreviationsResponse(
            total=len(abbreviations),
            abbreviations=abbreviations
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get abbreviations: {str(e)}"
        )


@app.post("/abbreviations")
async def update_abbreviations(
        request: AbbreviationUpdateRequest,
        matcher=Depends(get_matcher)
):
    """
    Add or update abbreviations.

    Merges new abbreviations with existing ones.
    Updates are persisted to disk.
    """
    try:
        # Update in-memory abbreviations
        matcher.abbreviation_expander.abbreviations.update(request.abbreviations)

        # Save to disk
        abbreviation_path = Path(matcher.config.abbreviation_dict_path)
        abbreviation_path.parent.mkdir(parents=True, exist_ok=True)

        with open(abbreviation_path, 'w') as f:
            json.dump(matcher.abbreviation_expander.abbreviations, f, indent=2)

        state.logger.info(f"Updated {len(request.abbreviations)} abbreviations")

        return {
            "success": True,
            "message": f"Added/updated {len(request.abbreviations)} abbreviations",
            "total_abbreviations": len(matcher.abbreviation_expander.abbreviations),
            "updated": list(request.abbreviations.keys())
        }

    except Exception as e:
        state.logger.error(f"Failed to update abbreviations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update abbreviations: {str(e)}"
        )


@app.delete("/abbreviations/{abbreviation}")
async def delete_abbreviation(
        abbreviation: str,
        matcher=Depends(get_matcher)
):
    """
    Delete a specific abbreviation.

    Changes are persisted to disk.
    """
    try:
        if abbreviation not in matcher.abbreviation_expander.abbreviations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Abbreviation '{abbreviation}' not found"
            )

        # Remove from memory
        expansion = matcher.abbreviation_expander.abbreviations.pop(abbreviation)

        # Save to disk
        abbreviation_path = Path(matcher.config.abbreviation_dict_path)
        with open(abbreviation_path, 'w') as f:
            json.dump(matcher.abbreviation_expander.abbreviations, f, indent=2)

        state.logger.info(f"Deleted abbreviation: {abbreviation} → {expansion}")

        return {
            "success": True,
            "message": f"Deleted abbreviation '{abbreviation}'",
            "deleted": {abbreviation: expansion},
            "total_abbreviations": len(matcher.abbreviation_expander.abbreviations)
        }

    except HTTPException:
        raise
    except Exception as e:
        state.logger.error(f"Failed to delete abbreviation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete abbreviation: {str(e)}"
        )


@app.post("/abbreviations/upload")
async def upload_abbreviations(
        file: UploadFile = File(..., description="JSON file with abbreviations"),
        replace: bool = False,
        matcher=Depends(get_matcher)
):
    """
    Upload abbreviations from JSON file.

    **File Format:**
```json
    {
      "cust": "customer",
      "txn": "transaction",
      "acct": "account"
    }
```

    **Parameters:**
    - `replace`: If true, replaces all existing abbreviations. If false, merges with existing.
    """
    try:
        # Validate file type
        if not file.filename.endswith('.json'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be JSON format"
            )

        # Read and parse JSON
        content = await file.read()
        new_abbreviations = json.loads(content)

        # Validate structure
        if not isinstance(new_abbreviations, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JSON must be a dictionary of abbreviation: expansion pairs"
            )

        # Validate all values are strings
        for key, value in new_abbreviations.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="All keys and values must be strings"
                )

        # Update abbreviations
        if replace:
            matcher.abbreviation_expander.abbreviations = new_abbreviations
            message = f"Replaced all abbreviations with {len(new_abbreviations)} new entries"
        else:
            matcher.abbreviation_expander.abbreviations.update(new_abbreviations)
            message = f"Merged {len(new_abbreviations)} abbreviations"

        # Save to disk
        abbreviation_path = Path(matcher.config.abbreviation_dict_path)
        abbreviation_path.parent.mkdir(parents=True, exist_ok=True)

        with open(abbreviation_path, 'w') as f:
            json.dump(matcher.abbreviation_expander.abbreviations, f, indent=2)

        state.logger.info(f"Uploaded abbreviations from {file.filename}")

        return {
            "success": True,
            "message": message,
            "filename": file.filename,
            "uploaded": len(new_abbreviations),
            "total_abbreviations": len(matcher.abbreviation_expander.abbreviations)
        }

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON format: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        state.logger.error(f"Failed to upload abbreviations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload abbreviations: {str(e)}"
        )


@app.get("/abbreviations/download")
async def download_abbreviations(matcher=Depends(get_matcher)):
    """
    Download current abbreviations as JSON file.
    """
    try:
        from starlette.responses import StreamingResponse
        import io

        # Create JSON content
        abbreviations_json = json.dumps(
            matcher.abbreviation_expander.abbreviations,
            indent=2
        )

        # Create file stream
        file_stream = io.BytesIO(abbreviations_json.encode())

        return StreamingResponse(
            file_stream,
            media_type="application/json",
            headers={
                "Content-Disposition": "attachment; filename=abbreviations.json"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download abbreviations: {str(e)}"
        )
# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "schema_matcher.api:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        log_level="info",
        access_log=True,
        reload=False  # Disable reload to avoid metric duplication
    )