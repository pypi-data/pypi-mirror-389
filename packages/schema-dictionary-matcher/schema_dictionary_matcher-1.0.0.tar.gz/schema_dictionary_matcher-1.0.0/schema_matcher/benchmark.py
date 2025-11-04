"""
Comprehensive Benchmarking Script for Advanced Schema Matcher
Measures: Latency, Precision, Cache Performance, Throughput
"""

import time
import json
import statistics
from pathlib import Path
from typing import List, Dict
import pandas as pd
import tempfile

from .config import AdvancedConfig
from .schema_matcher import AdvancedSchemaMatcher
from .models import DictionaryEntry


class PerformanceBenchmark:
    """Comprehensive performance benchmarking."""

    def __init__(self, matcher: AdvancedSchemaMatcher):
        self.matcher = matcher
        self.results = {
            "latency": [],
            "precision": [],
            "cache_hits": 0,
            "total_queries": 0,
            "decisions": {"AUTO_APPROVE": 0, "REVIEW": 0, "REJECT": 0}
        }

    def run_latency_benchmark(self, num_iterations: int = 100):
        """Measure latency distribution."""
        print("\n" + "=" * 80)
        print(f"LATENCY BENCHMARK ({num_iterations} iterations)")
        print("=" * 80)

        # Create test schema
        test_schema = {
            "type": "record",
            "name": "Test",
            "fields": [
                {"name": "email", "type": "string"},
                {"name": "amount", "type": "double"},
                {"name": "date", "type": "long"}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.avsc', delete=False) as f:
            json.dump(test_schema, f)
            schema_path = f.name

        latencies = []

        for i in range(num_iterations):
            start = time.time()
            results = self.matcher.match_avro_schema(schema_path)
            elapsed = (time.time() - start) * 1000

            latencies.append(elapsed)

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{num_iterations}")

        # Clean up
        Path(schema_path).unlink()

        # Calculate statistics
        p50 = statistics.median(latencies)
        p95 = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        p99 = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
        mean = statistics.mean(latencies)

        print(f"\nLatency Results:")
        print(f"  Mean:  {mean:.1f}ms")
        print(f"  P50:   {p50:.1f}ms")
        print(f"  P95:   {p95:.1f}ms")
        print(f"  P99:   {p99:.1f}ms")
        print(f"  Min:   {min(latencies):.1f}ms")
        print(f"  Max:   {max(latencies):.1f}ms")

        return {
            "mean": mean,
            "p50": p50,
            "p95": p95,
            "p99": p99,
            "min": min(latencies),
            "max": max(latencies)
        }

    def run_precision_benchmark(self, test_cases: List[Dict]):
        """Measure precision@K with ground truth."""
        print("\n" + "=" * 80)
        print(f"PRECISION BENCHMARK ({len(test_cases)} test cases)")
        print("=" * 80)

        precision_at_1 = []
        precision_at_3 = []
        precision_at_5 = []

        for i, test_case in enumerate(test_cases):
            # Create schema for this test
            schema = {
                "type": "record",
                "name": "Test",
                "fields": [
                    {
                        "name": test_case["field_name"],
                        "type": test_case["field_type"],
                        "doc": test_case.get("field_doc", "")
                    }
                ]
            }

            with tempfile.NamedTemporaryFile(mode='w', suffix='.avsc', delete=False) as f:
                json.dump(schema, f)
                schema_path = f.name

            # Run matching
            results = self.matcher.match_avro_schema(schema_path)

            # Clean up
            Path(schema_path).unlink()

            # Check precision
            ground_truth = test_case["expected_match_id"]

            # Get top-K results
            top_results = sorted(results, key=lambda x: x.final_confidence, reverse=True)[:5]
            matched_ids = [r.matched_entry.id for r in top_results]

            # Calculate precision
            p_at_1 = 1.0 if ground_truth in matched_ids[:1] else 0.0
            p_at_3 = 1.0 if ground_truth in matched_ids[:3] else 0.0
            p_at_5 = 1.0 if ground_truth in matched_ids[:5] else 0.0

            precision_at_1.append(p_at_1)
            precision_at_3.append(p_at_3)
            precision_at_5.append(p_at_5)

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{len(test_cases)}")

        p1 = statistics.mean(precision_at_1) * 100
        p3 = statistics.mean(precision_at_3) * 100
        p5 = statistics.mean(precision_at_5) * 100

        print(f"\nPrecision Results:")
        print(f"  Precision@1: {p1:.1f}%")
        print(f"  Precision@3: {p3:.1f}%")
        print(f"  Precision@5: {p5:.1f}%")

        return {
            "precision@1": p1,
            "precision@3": p3,
            "precision@5": p5
        }

    def run_cache_benchmark(self, num_queries: int = 1000):
        """Measure cache performance."""
        print("\n" + "=" * 80)
        print(f"CACHE BENCHMARK ({num_queries} queries)")
        print("=" * 80)

        if not self.matcher.cache:
            print("  ⚠️  Hierarchical cache not enabled")
            return {}

        # Clear cache first
        self.matcher.cache.clear()

        # Queries with some repetition
        queries = [
            "customer email",
            "transaction amount",
            "account balance",
            "customer phone",
            "customer email",  # Repeat
            "transaction date",
            "customer email",  # Repeat
            "account number"
        ]

        latencies_cold = []
        latencies_hot = []

        for i in range(num_queries):
            query = queries[i % len(queries)]

            # Create schema
            schema = {
                "type": "record",
                "name": "Test",
                "fields": [{"name": query.replace(" ", "_"), "type": "string"}]
            }

            with tempfile.NamedTemporaryFile(mode='w', suffix='.avsc', delete=False) as f:
                json.dump(schema, f)
                schema_path = f.name

            start = time.time()
            results = self.matcher.match_avro_schema(schema_path)
            elapsed = (time.time() - start) * 1000

            Path(schema_path).unlink()

            # Track cache hits
            if results and results[0].cache_hit:
                latencies_hot.append(elapsed)
            else:
                latencies_cold.append(elapsed)

            if (i + 1) % 100 == 0:
                print(f"  Progress: {i + 1}/{num_queries}")

        # Get cache stats
        stats = self.matcher.cache.get_stats()

        print(f"\nCache Performance:")
        print(f"  Total Queries: {stats.total_queries}")
        print(f"  L1 Hits: {stats.l1_hits} ({stats.l1_hit_rate:.1%})")
        print(f"  L2 Hits: {stats.l2_hits}")
        print(f"  L3 Hits: {stats.l3_hits}")
        print(f"  Cache Misses: {stats.misses}")
        print(f"  Overall Hit Rate: {stats.hit_rate:.1%}")

        if latencies_cold:
            print(f"\n  Avg Latency (Cold): {statistics.mean(latencies_cold):.1f}ms")
        if latencies_hot:
            print(f"  Avg Latency (Hot):  {statistics.mean(latencies_hot):.1f}ms")
            if latencies_cold:
                speedup = statistics.mean(latencies_cold) / statistics.mean(latencies_hot)
                print(f"  Cache Speedup: {speedup:.1f}x")

        return {
            "hit_rate": stats.hit_rate,
            "l1_hits": stats.l1_hits,
            "l2_hits": stats.l2_hits,
            "l3_hits": stats.l3_hits,
            "cold_latency": statistics.mean(latencies_cold) if latencies_cold else None,
            "hot_latency": statistics.mean(latencies_hot) if latencies_hot else None
        }

    def run_throughput_benchmark(self, duration_seconds: int = 60):
        """Measure queries per second."""
        print("\n" + "=" * 80)
        print(f"THROUGHPUT BENCHMARK ({duration_seconds}s)")
        print("=" * 80)

        # Create test schema
        schema = {
            "type": "record",
            "name": "Test",
            "fields": [
                {"name": "email", "type": "string"},
                {"name": "amount", "type": "double"}
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.avsc', delete=False) as f:
            json.dump(schema, f)
            schema_path = f.name

        start_time = time.time()
        query_count = 0

        while (time.time() - start_time) < duration_seconds:
            self.matcher.match_avro_schema(schema_path)
            query_count += 1

            if query_count % 10 == 0:
                elapsed = time.time() - start_time
                qps = query_count / elapsed
                print(f"  Progress: {elapsed:.1f}s, QPS: {qps:.1f}", end='\r')

        Path(schema_path).unlink()

        total_time = time.time() - start_time
        qps = query_count / total_time

        print(f"\nThroughput Results:")
        print(f"  Total Queries: {query_count}")
        print(f"  Total Time: {total_time:.1f}s")
        print(f"  QPS: {qps:.1f}")

        return {
            "total_queries": query_count,
            "duration": total_time,
            "qps": qps
        }

    def generate_report(self, output_path: str = "./benchmark_report.json"):
        """Generate comprehensive benchmark report."""
        print("\n" + "=" * 80)
        print("GENERATING COMPREHENSIVE REPORT")
        print("=" * 80)

        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "configuration": {
                "embedding_model": self.matcher.config.embedding_model,
                "quantization": self.matcher.config.quantization_type,
                "colbert_maxsim": self.matcher.config.colbert_use_maxsim,
                "hierarchical_cache": self.matcher.config.use_hierarchical_cache,
                "type_aware": self.matcher.config.use_type_aware_embeddings,
                "incremental_updates": self.matcher.config.use_incremental_updates,
                "graph_refinement": self.matcher.config.use_graph_refinement
            }
        }

        # Run all benchmarks
        report["latency"] = self.run_latency_benchmark(num_iterations=50)
        report["cache"] = self.run_cache_benchmark(num_queries=500)
        report["throughput"] = self.run_throughput_benchmark(duration_seconds=30)

        # Save report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n✅ Report saved to: {output_path}")

        return report


def main():
    """Run comprehensive benchmarks."""
    print("\n" + "=" * 80)
    print("ADVANCED SCHEMA MATCHER - PERFORMANCE BENCHMARK")
    print("=" * 80)

    # Initialize matcher
    config = AdvancedConfig(
        log_level="WARNING",  # Reduce noise during benchmarking
        use_hierarchical_cache=True,
        use_incremental_updates=True,
        use_graph_refinement=True,
        colbert_use_maxsim=True
    )

    matcher = AdvancedSchemaMatcher(config)

    # Create and load sample dictionary
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

    # Sync dictionary
    print("\nSyncing dictionary...")
    matcher.sync_excel_to_vector_db(excel_path, force_rebuild=True)
    Path(excel_path).unlink()

    # Run benchmarks
    benchmark = PerformanceBenchmark(matcher)
    report = benchmark.generate_report()

    # Print summary
    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"Mean Latency: {report['latency']['mean']:.1f}ms")
    print(f"P95 Latency: {report['latency']['p95']:.1f}ms")
    print(f"Cache Hit Rate: {report['cache']['hit_rate']:.1%}")
    print(f"Throughput: {report['throughput']['qps']:.1f} QPS")
    print("=" * 80)


if __name__ == "__main__":
    main()