"""
Realistic Performance Benchmark - Varied queries, no cache pollution
"""

import time
import json
import statistics
from pathlib import Path
import tempfile
import pandas as pd

from .config import AdvancedConfig
from .schema_matcher import AdvancedSchemaMatcher


def run_realistic_benchmark():
    """Run realistic benchmark with varied queries."""

    print("\n" + "=" * 80)
    print("REALISTIC PERFORMANCE BENCHMARK")
    print("=" * 80)

    # Initialize matcher WITHOUT cache for accurate measurements
    config = AdvancedConfig(
        log_level="ERROR",  # Reduce noise
        use_hierarchical_cache=False,  # Disable cache for accurate latency
        use_incremental_updates=True,
        use_graph_refinement=False,  # Disable for cleaner benchmark
        colbert_use_maxsim=True,
        use_type_aware_embeddings=True
    )

    matcher = AdvancedSchemaMatcher(config)

    # Load sample dictionary
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

    print("\n1. Syncing dictionary...")
    matcher.sync_excel_to_vector_db(excel_path, force_rebuild=True)
    Path(excel_path).unlink()

    # Varied test queries (realistic field names)
    test_queries = [
        ("customer_email", "string", "Email address for the customer"),
        ("user_email", "string", "User's email"),
        ("email_addr", "string", "Email"),
        ("first_name", "string", "First name"),
        ("fname", "string", "First name"),
        ("given_name", "string", "Given name"),
        ("last_name", "string", "Last name"),
        ("surname", "string", "Surname"),
        ("transaction_amt", "double", "Transaction amount in USD"),
        ("txn_amount", "double", "Amount"),
        ("amount", "double", "Amount"),
        ("transaction_dt", "long", "Transaction date"),
        ("txn_date", "long", "Date of transaction"),
        ("acct_balance", "double", "Account balance"),
        ("balance", "double", "Balance"),
        ("account_num", "string", "Account number"),
        ("acct_id", "string", "Account identifier"),
        ("phone_number", "string", "Phone"),
        ("mobile", "string", "Mobile phone"),
        ("street_address", "string", "Street address"),
        ("address1", "string", "Address line 1"),
        ("city", "string", "City"),
        ("state", "string", "State"),
        ("zip", "string", "Zip code"),
        ("postal_code", "string", "Postal code")
    ]

    print(f"\n2. Running {len(test_queries)} varied queries...")

    latencies = []
    confidences = []
    decisions = {"AUTO_APPROVE": 0, "REVIEW": 0, "REJECT": 0}

    for i, (field_name, field_type, field_doc) in enumerate(test_queries):
        # Create schema
        schema = {
            "type": "record",
            "name": "Test",
            "fields": [
                {"name": field_name, "type": field_type, "doc": field_doc}
            ]
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

        # Get top result
        if results:
            top_result = [r for r in results if r.rank == 1][0]
            confidences.append(top_result.final_confidence)
            decisions[top_result.decision] += 1

        if (i + 1) % 5 == 0:
            print(f"  Progress: {i + 1}/{len(test_queries)}")

    # Calculate statistics
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    print(f"\nLatency Statistics:")
    print(f"  Mean:  {statistics.mean(latencies):.1f}ms")
    print(f"  Median: {statistics.median(latencies):.1f}ms")
    print(f"  P95:   {statistics.quantiles(latencies, n=20)[18]:.1f}ms")
    print(f"  P99:   {statistics.quantiles(latencies, n=100)[98]:.1f}ms")
    print(f"  Min:   {min(latencies):.1f}ms")
    print(f"  Max:   {max(latencies):.1f}ms")

    print(f"\nConfidence Statistics:")
    print(f"  Mean:  {statistics.mean(confidences):.1%}")
    print(f"  Median: {statistics.median(confidences):.1%}")
    print(f"  Min:   {min(confidences):.1%}")
    print(f"  Max:   {max(confidences):.1%}")

    print(f"\nDecision Distribution:")
    total = sum(decisions.values())
    for decision, count in decisions.items():
        print(f"  {decision}: {count} ({count / total * 100:.1f}%)")

    # Performance vs Target
    print(f"\nPerformance vs Target:")
    target_latency = 230  # ms
    mean_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18]

    if mean_latency < target_latency:
        print(f"  ✅ Mean latency {mean_latency:.0f}ms is {target_latency - mean_latency:.0f}ms below target")
    else:
        print(f"  ❌ Mean latency {mean_latency:.0f}ms is {mean_latency - target_latency:.0f}ms above target")

    if p95_latency < target_latency:
        print(f"  ✅ P95 latency {p95_latency:.0f}ms is {target_latency - p95_latency:.0f}ms below target")
    else:
        print(f"  ❌ P95 latency {p95_latency:.0f}ms is {p95_latency - target_latency:.0f}ms above target")

    target_auto_approve = 0.80  # 80%
    auto_approve_rate = decisions["AUTO_APPROVE"] / total

    if auto_approve_rate >= target_auto_approve:
        print(f"  ✅ Auto-approval rate {auto_approve_rate:.1%} meets target")
    else:
        print(f"  ⚠️  Auto-approval rate {auto_approve_rate:.1%} is below target {target_auto_approve:.0%}")

    print("=" * 80)

    return {
        "mean_latency": mean_latency,
        "p95_latency": p95_latency,
        "mean_confidence": statistics.mean(confidences),
        "auto_approve_rate": auto_approve_rate
    }


if __name__ == "__main__":
    results = run_realistic_benchmark()