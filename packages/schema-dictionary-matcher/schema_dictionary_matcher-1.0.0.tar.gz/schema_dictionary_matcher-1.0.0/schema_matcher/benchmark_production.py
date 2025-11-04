"""
Production Benchmark - Test production config
"""

import time
import json
import statistics
from pathlib import Path
import tempfile
import pandas as pd
import sys

# Import production config
sys.path.insert(0, 'advanced_schema_matcher')
from .config_production import ProductionConfig
from .schema_matcher import AdvancedSchemaMatcher


def warm_up_matcher(matcher):
    """Pre-load models to avoid cold start in benchmark."""
    print("Warming up (pre-loading models)...")

    # Create dummy schema to trigger model loading
    schema = {
        "type": "record",
        "name": "Warmup",
        "fields": [{"name": "test", "type": "string"}]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.avsc', delete=False) as f:
        json.dump(schema, f)
        schema_path = f.name

    # Run once to load all models
    matcher.match_avro_schema(schema_path)
    Path(schema_path).unlink()

    print("Warmup complete!")


def run_production_benchmark():
    """Run benchmark with production config."""

    print("\n" + "=" * 80)
    print("PRODUCTION CONFIGURATION BENCHMARK")
    print("=" * 80)

    # Use production config
    config = ProductionConfig()

    # Override for testing
    config.use_hierarchical_cache = False  # Test without cache first
    config.log_level = "ERROR"

    matcher = AdvancedSchemaMatcher(config)

    # Load dictionary
    data = {
        "ID": [f"field_{i:03d}" for i in range(1, 16)],
        "Business Name": [
            "Customer Email Address", "Customer First Name", "Customer Last Name",
            "Transaction Amount", "Transaction Date", "Account Balance",
            "Account Number", "Phone Number", "Address Line 1",
            "City Name", "State Code", "Zip Code",
            "Customer ID", "Transaction ID", "Account Type"
        ],
        "Logical Name": [
            "cust_email", "cust_first_name", "cust_last_name",
            "txn_amt", "txn_date", "acct_bal",
            "acct_num", "phone_num", "addr_line1",
            "city_name", "state_code", "zip_code",
            "cust_id", "txn_id", "acct_type"
        ],
        "Definition": [
            "Email address for customer", "First name of customer", "Last name of customer",
            "Amount of transaction", "Date of transaction", "Current account balance",
            "Account number", "Phone number", "Address line 1",
            "City name", "State code", "Zip code",
            "Customer identifier", "Transaction identifier", "Account type"
        ],
        "Data Type": ["string"] * 15,
        "Protection Level": ["PII"] * 15
    }
    df = pd.DataFrame(data)

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        df.to_excel(f.name, index=False)
        excel_path = f.name

    print("\n1. Loading dictionary...")
    matcher.sync_excel_to_vector_db(excel_path, force_rebuild=True)
    Path(excel_path).unlink()

    # CRITICAL: Warm up to avoid cold start affecting benchmark
    warm_up_matcher(matcher)

    # Test queries
    test_queries = [
        ("customer_email", "string", "Email address"),
        ("email", "string", "Email"),
        ("first_name", "string", "First name"),
        ("fname", "string", "First name"),
        ("last_name", "string", "Last name"),
        ("transaction_amt", "double", "Transaction amount"),
        ("amount", "double", "Amount"),
        ("transaction_date", "long", "Date"),
        ("acct_balance", "double", "Balance"),
        ("balance", "double", "Balance"),
        ("account_num", "string", "Account number"),
        ("phone", "string", "Phone"),
        ("street", "string", "Street"),
        ("city", "string", "City"),
        ("state", "string", "State"),
    ]

    print(f"\n2. Running {len(test_queries)} queries (AFTER warmup)...")

    latencies = []
    confidences = []
    decisions = {"AUTO_APPROVE": 0, "REVIEW": 0, "REJECT": 0}

    for i, (field_name, field_type, field_doc) in enumerate(test_queries):
        schema = {
            "type": "record",
            "name": "Test",
            "fields": [{"name": field_name, "type": field_type, "doc": field_doc}]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.avsc', delete=False) as f:
            json.dump(schema, f)
            schema_path = f.name

        # Measure latency
        start = time.time()
        results = matcher.match_avro_schema(schema_path)
        elapsed = (time.time() - start) * 1000

        Path(schema_path).unlink()

        latencies.append(elapsed)

        if results:
            top = results[0]
            confidences.append(top.final_confidence)
            decisions[top.decision] += 1

        if (i + 1) % 5 == 0:
            print(f"  Progress: {i + 1}/{len(test_queries)}")

    # Results
    print("\n" + "=" * 80)
    print("PRODUCTION RESULTS")
    print("=" * 80)

    mean_lat = statistics.mean(latencies)
    median_lat = statistics.median(latencies)
    p95_lat = statistics.quantiles(latencies, n=20)[18]
    p99_lat = statistics.quantiles(latencies, n=100)[98]

    print(f"\nLatency:")
    print(f"  Mean:   {mean_lat:.1f}ms")
    print(f"  Median: {median_lat:.1f}ms")
    print(f"  P95:    {p95_lat:.1f}ms")
    print(f"  P99:    {p99_lat:.1f}ms")
    print(f"  Min:    {min(latencies):.1f}ms")
    print(f"  Max:    {max(latencies):.1f}ms")

    print(f"\nConfidence:")
    print(f"  Mean:   {statistics.mean(confidences):.1%}")
    print(f"  Median: {statistics.median(confidences):.1%}")
    print(f"  Min:    {min(confidences):.1%}")
    print(f"  Max:    {max(confidences):.1%}")

    print(f"\nDecisions:")
    total = sum(decisions.values())
    for decision, count in decisions.items():
        print(f"  {decision}: {count} ({count / total * 100:.1f}%)")

    # Check targets
    print(f"\nTargets:")
    target_p95 = 230
    target_auto = 0.70

    auto_rate = decisions["AUTO_APPROVE"] / total

    if p95_lat < target_p95:
        print(f"  ✅ P95 latency {p95_lat:.0f}ms < {target_p95}ms")
    else:
        print(f"  ❌ P95 latency {p95_lat:.0f}ms > {target_p95}ms (need {p95_lat - target_p95:.0f}ms improvement)")

    if auto_rate >= target_auto:
        print(f"  ✅ Auto-approval {auto_rate:.1%} >= {target_auto:.0%}")
    else:
        print(f"  ⚠️  Auto-approval {auto_rate:.1%} < {target_auto:.0%}")

    print("=" * 80)


if __name__ == "__main__":
    run_production_benchmark()