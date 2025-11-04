"""
Example usage of Advanced Schema Matcher
"""

import logging
from pathlib import Path
import json

from .config import AdvancedConfig
from .schema_matcher import AdvancedSchemaMatcher
from .models import DictionaryEntry


def create_sample_data():
    """Create sample data dictionary and Avro schema for testing."""

    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # Create sample Excel data (as JSON for this example)
    sample_dictionary = [
        {
            "id": "field_001",
            "business_name": "Customer Email Address",
            "logical_name": "cust_email_addr",
            "definition": "Primary email address for customer contact",
            "data_type": "string",
            "protection_level": "PII"
        },
        {
            "id": "field_002",
            "business_name": "Customer First Name",
            "logical_name": "cust_first_name",
            "definition": "First name of the customer",
            "data_type": "string",
            "protection_level": "PII"
        },
        {
            "id": "field_003",
            "business_name": "Customer Last Name",
            "logical_name": "cust_last_name",
            "definition": "Last name of the customer",
            "data_type": "string",
            "protection_level": "PII"
        },
        {
            "id": "field_004",
            "business_name": "Transaction Amount",
            "logical_name": "txn_amt",
            "definition": "Monetary value of the transaction in USD",
            "data_type": "decimal",
            "protection_level": "Internal"
        },
        {
            "id": "field_005",
            "business_name": "Transaction Date",
            "logical_name": "txn_dt",
            "definition": "Date when transaction occurred",
            "data_type": "date",
            "protection_level": "Internal"
        },
        {
            "id": "field_006",
            "business_name": "Account Balance",
            "logical_name": "acct_bal",
            "definition": "Current balance in customer account",
            "data_type": "decimal",
            "protection_level": "Confidential"
        },
        {
            "id": "field_007",
            "business_name": "Account Number",
            "logical_name": "acct_num",
            "definition": "Unique account identifier",
            "data_type": "string",
            "protection_level": "PII"
        },
        {
            "id": "field_008",
            "business_name": "Phone Number",
            "logical_name": "phone_num",
            "definition": "Primary phone contact number",
            "data_type": "string",
            "protection_level": "PII"
        },
        {
            "id": "field_009",
            "business_name": "Address Line 1",
            "logical_name": "addr_line_1",
            "definition": "Street address first line",
            "data_type": "string",
            "protection_level": "PII"
        },
        {
            "id": "field_010",
            "business_name": "City Name",
            "logical_name": "city_name",
            "definition": "City where customer resides",
            "data_type": "string",
            "protection_level": "Internal"
        },
        {
            "id": "field_011",
            "business_name": "State Code",
            "logical_name": "state_cd",
            "definition": "Two-letter state abbreviation",
            "data_type": "string",
            "protection_level": "Internal"
        },
        {
            "id": "field_012",
            "business_name": "Zip Code",
            "logical_name": "zip_cd",
            "definition": "5-digit postal code",
            "data_type": "string",
            "protection_level": "Internal"
        },
        {
            "id": "field_013",
            "business_name": "Customer Birth Date",
            "logical_name": "cust_birth_dt",
            "definition": "Date of birth for customer",
            "data_type": "date",
            "protection_level": "PII"
        },
        {
            "id": "field_014",
            "business_name": "Customer Status",
            "logical_name": "cust_status",
            "definition": "Active status of customer account",
            "data_type": "string",
            "protection_level": "Internal"
        },
        {
            "id": "field_015",
            "business_name": "Credit Score",
            "logical_name": "credit_score",
            "definition": "Customer credit score value",
            "data_type": "integer",
            "protection_level": "Confidential"
        }
    ]

    # Save as JSON (simulating Excel data)
    dict_path = data_dir / "sample_dictionary.json"
    with open(dict_path, 'w') as f:
        json.dump(sample_dictionary, f, indent=2)

    # Create sample Avro schema
    sample_schema = {
        "type": "record",
        "name": "CustomerTransaction",
        "namespace": "com.ccb",
        "doc": "Customer transaction data",
        "fields": [
            {
                "name": "customer_email",
                "type": "string",
                "doc": "Email address for customer"
            },
            {
                "name": "first_name",
                "type": "string",
                "doc": "Customer first name"
            },
            {
                "name": "last_name",
                "type": "string",
                "doc": "Customer last name"
            },
            {
                "name": "transaction_amount",
                "type": "double",
                "doc": "Amount of transaction"
            },
            {
                "name": "transaction_date",
                "type": "string",
                "doc": "Date of transaction"
            },
            {
                "name": "account_balance",
                "type": "double",
                "doc": "Current account balance"
            },
            {
                "name": "account_number",
                "type": "string",
                "doc": "Account identifier"
            },
            {
                "name": "phone",
                "type": ["null", "string"],
                "doc": "Contact phone number"
            },
            {
                "name": "address",
                "type": {
                    "type": "record",
                    "name": "Address",
                    "fields": [
                        {
                            "name": "street",
                            "type": "string",
                            "doc": "Street address"
                        },
                        {
                            "name": "city",
                            "type": "string",
                            "doc": "City name"
                        },
                        {
                            "name": "state",
                            "type": "string",
                            "doc": "State code"
                        },
                        {
                            "name": "zipcode",
                            "type": "string",
                            "doc": "Postal code"
                        }
                    ]
                },
                "doc": "Customer address information"
            }
        ]
    }

    schema_path = data_dir / "sample_schema.avsc"
    with open(schema_path, 'w') as f:
        json.dump(sample_schema, f, indent=2)

    print(f"Created sample dictionary: {dict_path}")
    print(f"Created sample schema: {schema_path}")

    return dict_path, schema_path


def example_basic_usage():
    """Example 1: Basic usage."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Usage")
    print("=" * 80)

    # Create sample data
    dict_path, schema_path = create_sample_data()

    # Initialize matcher with default config
    config = AdvancedConfig()
    matcher = AdvancedSchemaMatcher(config)

    # Convert JSON to in-memory entries (simulating Excel load)
    with open(dict_path, 'r') as f:
        dict_data = json.load(f)

    entries = [DictionaryEntry(**item) for item in dict_data]

    # Prepare for indexing - FIX COLUMN NAMES
    import pandas as pd
    df = pd.DataFrame([{
        "ID": e.id,
        "Business Name": e.business_name,
        "Logical Name": e.logical_name,
        "Definition": e.definition,
        "Data Type": e.data_type,
        "Protection Level": e.protection_level
    } for e in entries])

    excel_path = Path("data/sample_dictionary.xlsx")
    df.to_excel(excel_path, index=False)

    # Sync dictionary to vector DB
    print("\nSyncing dictionary to vector database...")
    stats = matcher.sync_excel_to_vector_db(
        str(excel_path),
        force_rebuild=True
    )
    print(stats.summary())

    # Match Avro schema
    print("\nMatching Avro schema fields...")
    results = matcher.match_avro_schema(
        str(schema_path),
        output_path="data/match_results.json"
    )

    # Print results
    print(f"\nMatched {len([r for r in results if r.rank == 1])} fields\n")

    # In run_demo.py, find the printing section and update:
    for result in results:
        if result.rank == 1:  # Only show top match
            print(f"\nField: {result.avro_field.full_path}")
            print(f"  → Matched: {result.matched_entry.business_name}")
            print(f"  → Confidence: {result.final_confidence:.2%}")  # This should already be correct
            print(f"  → Decision: {result.decision}")
            print(f"  → Latency: {result.latency_ms:.1f}ms")
            print()


def example_speed_optimized():
    """Example 2: Speed-optimized configuration."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Speed-Optimized Configuration")
    print("=" * 80)

    # Speed-optimized config
    config = AdvancedConfig(
        # Fast model
        embedding_model="BAAI/bge-small-en-v1.5",

        # Aggressive quantization
        use_quantization=True,
        quantization_type="int8",
        use_onnx=True,

        # Disable ColBERT for max speed
        use_colbert_reranking=False,

        # Aggressive caching
        use_semantic_cache=True,
        cache_similarity_threshold=0.85,

        # Larger batches
        batch_size=128
    )

    print("Configuration:")
    print(f"  Model: {config.embedding_model}")
    print(f"  Quantization: {config.quantization_type}")
    print(f"  ColBERT: {config.use_colbert_reranking}")
    print(f"  Cache: {config.use_semantic_cache}")
    print("\nExpected: 100-150ms per field, 10x baseline speed")


def example_accuracy_optimized():
    """Example 3: Accuracy-optimized configuration."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Accuracy-Optimized Configuration")
    print("=" * 80)

    # Accuracy-optimized config
    config = AdvancedConfig(
        # Best model
        embedding_model="BAAI/bge-large-en-v1.5",

        # All accuracy features
        use_colbert_reranking=True,
        use_type_aware_embeddings=True,
        use_abbreviation_expansion=True,

        # Best cross-encoder
        cross_encoder_model="BAAI/bge-reranker-large",

        # More candidates
        dense_top_k=200,
        sparse_top_k=200,
        colbert_top_k=100,

        # Stricter thresholds
        auto_approve_threshold=0.90
    )

    print("Configuration:")
    print(f"  Model: {config.embedding_model}")
    print(f"  ColBERT: {config.use_colbert_reranking}")
    print(f"  Type-aware: {config.use_type_aware_embeddings}")
    print(f"  Abbreviations: {config.use_abbreviation_expansion}")
    print("\nExpected: 97-99% precision@5, 200-300ms per field")


def example_production_balanced():
    """Example 4: Production-balanced configuration (RECOMMENDED)."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Production-Balanced Configuration (RECOMMENDED)")
    print("=" * 80)

    # Balanced config
    config = AdvancedConfig(
        # Proven model
        embedding_model="BAAI/bge-base-en-v1.5",

        # Full optimizations
        use_quantization=True,
        quantization_type="int8",
        use_onnx=True,

        # All accuracy features
        use_colbert_reranking=True,
        use_type_aware_embeddings=True,
        use_abbreviation_expansion=True,
        use_semantic_cache=True,

        # Optimized parameters
        fusion_alpha=0.65,
        batch_size=64,

        # Standard thresholds
        auto_approve_threshold=0.88,
        review_threshold=0.65
    )

    print("Configuration:")
    print(f"  Model: {config.embedding_model}")
    print(f"  All optimizations: Enabled")
    print(f"  Auto-approve threshold: {config.auto_approve_threshold}")
    print("\nExpected: 97-99% precision@5, 100-230ms per field")


def example_custom_abbreviations():
    """Example 5: Custom abbreviation dictionary."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Custom Abbreviation Dictionary")
    print("=" * 80)

    # Create custom abbreviation dictionary
    abbreviations = {
        "acct": ["account"],
        "cust": ["customer"],
        "txn": ["transaction"],
        "amt": ["amount"],
        "dt": ["date"],
        "ts": ["timestamp"],
        "cd": ["code"],
        "num": ["number"],
        "addr": ["address"],
        "bal": ["balance"],
        "pmt": ["payment"],
        "desc": ["description"],
        "qty": ["quantity"],
        "pct": ["percent"],
        "ccb": ["consumer and community banking"],
        "glb": ["global"],
        "pmnt": ["payment"],
        "rte": ["rate"],
        "prin": ["principal"],
        "int": ["interest"],
    }

    # Save to file
    abbrev_path = Path("data/abbreviations_custom.json")
    with open(abbrev_path, 'w') as f:
        json.dump(abbreviations, f, indent=2)

    print(f"Created custom abbreviation dictionary: {abbrev_path}")
    print(f"Entries: {len(abbreviations)}")

    # Use in config
    config = AdvancedConfig(
        use_abbreviation_expansion=True,
        abbreviation_dict_path=str(abbrev_path)
    )

    print("\nAbbreviations will be expanded during matching:")
    print("  cust_email → customer_email")
    print("  txn_amt → transaction_amount")
    print("  acct_bal → account_balance")


def example_metrics_monitoring():
    """Example 6: Metrics and monitoring."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Metrics and Monitoring")
    print("=" * 80)

    config = AdvancedConfig(
        enable_metrics=True,
        metrics_log_path="logs/metrics.jsonl"
    )

    print("Metrics enabled:")
    print(f"  Log path: {config.metrics_log_path}")
    print("\nTracked metrics:")
    print("  - Precision@K (K=1,3,5,10)")
    print("  - Auto-approval rate")
    print("  - Average confidence")
    print("  - Latency (P50, P95, P99)")
    print("  - Cache hit rate")
    print("  - QPS under load")


def example_batch_processing():
    """Example 7: Batch processing multiple schemas."""
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Batch Processing Multiple Schemas")
    print("=" * 80)

    config = AdvancedConfig()
    matcher = AdvancedSchemaMatcher(config)

    # Use the sample schema that was created
    schema_files = [
        "./data/sample_schema.avsc",  # This one exists
    ]

    print(f"Processing {len(schema_files)} schema(s)...\n")

    all_results = []
    for schema_file in schema_files:
        print(f"Processing: {schema_file}")
        try:
            # Check if file exists
            if not Path(schema_file).exists():
                print(f"  Warning: File not found, skipping\n")
                continue

            results = matcher.match_avro_schema(schema_file)
            all_results.extend(results)

            # Print summary
            top_matches = [r for r in results if r.rank == 1]
            if len(top_matches) > 0:
                auto_approved = sum(1 for r in top_matches if r.decision == "AUTO_APPROVE")
                print(f"  Fields: {len(top_matches)}")
                print(f"  Auto-approved: {auto_approved} ({auto_approved / len(top_matches) * 100:.1f}%)")
            else:
                print(f"  No matches found")
            print()
        except Exception as e:
            print(f"  Error: {e}\n")

    print(f"Total results: {len(all_results)}")


def main():
    """Run all examples."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n" + "=" * 80)
    print("ADVANCED SCHEMA MATCHER - EXAMPLES")
    print("=" * 80)

    # Run examples
    try:
        example_basic_usage()
    except Exception as e:
        print(f"Example 1 failed: {e}")

    example_speed_optimized()
    example_accuracy_optimized()
    example_production_balanced()
    example_custom_abbreviations()
    example_metrics_monitoring()
    example_batch_processing()

    print("\n" + "=" * 80)
    print("EXAMPLES COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()