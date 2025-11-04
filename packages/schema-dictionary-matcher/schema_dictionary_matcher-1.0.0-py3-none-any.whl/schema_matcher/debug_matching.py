"""
Debug why matching accuracy is so poor
"""

import json
import tempfile
from pathlib import Path
import pandas as pd

from .config import AdvancedConfig
from .schema_matcher import AdvancedSchemaMatcher


def debug_single_match():
    """Debug a single match in detail."""

    print("\n" + "=" * 80)
    print("DETAILED MATCH DEBUGGING")
    print("=" * 80)

    # Config with detailed logging
    config = AdvancedConfig(
        log_level="INFO",
        use_colbert_reranking=False,  # Disable ColBERT
        use_hierarchical_cache=False,
        use_incremental_updates=False
    )

    matcher = AdvancedSchemaMatcher(config)

    # Load simple test dictionary
    data = {
        "ID": ["field_001", "field_002", "field_003"],
        "Business Name": ["Customer Email Address", "Transaction Amount", "Account Balance"],
        "Logical Name": ["cust_email", "txn_amt", "acct_bal"],
        "Definition": ["Email address for customer", "Transaction amount in dollars", "Current account balance"],
        "Data Type": ["string", "double", "double"],
        "Protection Level": ["PII", "Internal", "Internal"]
    }
    df = pd.DataFrame(data)

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        df.to_excel(f.name, index=False)
        excel_path = f.name

    print("\n1. Loading dictionary...")
    matcher.sync_excel_to_vector_db(excel_path, force_rebuild=True)
    Path(excel_path).unlink()

    # Test a query that SHOULD match
    print("\n2. Testing query: 'customer_email' -> should match 'Customer Email Address'")

    schema = {
        "type": "record",
        "name": "Test",
        "fields": [
            {
                "name": "customer_email",
                "type": "string",
                "doc": "Email address for the customer"
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.avsc', delete=False) as f:
        json.dump(schema, f)
        schema_path = f.name

    results = matcher.match_avro_schema(schema_path)
    Path(schema_path).unlink()

    print("\n3. Results:")
    print(f"{'Rank':<6} {'Match':<35} {'Confidence':<12} {'Decision':<12}")
    print("-" * 70)

    for result in results[:5]:  # Top 5
        symbol = "✓" if result.matched_entry.id == "field_001" else "✗"
        print(
            f"{symbol} {result.rank:<4} {result.matched_entry.business_name:<35} {result.final_confidence:<12.1%} {result.decision:<12}")

    # Show score breakdown for top match
    top = results[0]
    print(f"\n4. Score breakdown for top match:")
    print(f"   Semantic:         {top.semantic_score:.3f}")
    print(f"   Lexical:          {top.lexical_score:.3f}")
    print(f"   Edit Distance:    {top.edit_distance_score:.3f}")
    print(f"   Type Compat:      {top.type_compatibility_score:.3f}")
    print(f"   Final Confidence: {top.final_confidence:.3f}")

    # Test with different queries
    test_cases = [
        ("email", "string", "Email", "field_001"),
        ("transaction_amount", "double", "Transaction amount", "field_002"),
        ("balance", "double", "Balance", "field_003"),
    ]

    print("\n5. Testing other queries:")
    print(f"{'Query':<25} {'Expected':<25} {'Got':<25} {'Status':<10}")
    print("-" * 90)

    for field_name, field_type, doc, expected_id in test_cases:
        schema = {
            "type": "record",
            "name": "Test",
            "fields": [{"name": field_name, "type": field_type, "doc": doc}]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.avsc', delete=False) as f:
            json.dump(schema, f)
            schema_path = f.name

        results = matcher.match_avro_schema(schema_path)
        Path(schema_path).unlink()

        if results:
            top = results[0]
            status = "✓ CORRECT" if top.matched_entry.id == expected_id else "✗ WRONG"

            # Get expected entry name
            expected_name = data["Business Name"][int(expected_id.split("_")[1]) - 1]

            print(f"{field_name:<25} {expected_name:<25} {top.matched_entry.business_name:<25} {status:<10}")


def check_embeddings():
    """Check if embeddings are being generated correctly."""

    print("\n" + "=" * 80)
    print("EMBEDDING QUALITY CHECK")
    print("=" * 80)

    from embedding_generator import AdvancedEmbeddingGenerator

    config = AdvancedConfig(use_type_aware_embeddings=True)
    gen = AdvancedEmbeddingGenerator(config)

    # Test similar texts
    texts = [
        "Customer Email Address",
        "customer_email",
        "email",
        "Transaction Amount",
        "Account Balance"
    ]

    print("\n1. Generating embeddings...")
    embeddings = gen.encode(texts)

    print(f"\n2. Embedding dimension: {embeddings.shape[1]}")
    print(f"   Expected: 800 (768 base + 32 type-aware)")

    # Check similarity between similar items
    from sklearn.metrics.pairwise import cosine_similarity

    print("\n3. Similarity matrix:")
    print(f"{'':.<30}", end="")
    for text in texts:
        print(f"{text[:15]:<17}", end="")
    print()

    for i, text1 in enumerate(texts):
        print(f"{text1[:30]:.<30}", end="")
        for j, text2 in enumerate(texts):
            sim = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
            color = "✓" if sim > 0.7 and i != j else " "
            print(f"{color}{sim:.3f}           ", end="")
        print()

    print("\n4. Analysis:")
    # Check if "Customer Email Address" is most similar to "customer_email"
    email_full = embeddings[0]
    email_short = embeddings[1]
    email_minimal = embeddings[2]

    sim_full_short = cosine_similarity([email_full], [email_short])[0][0]
    sim_full_minimal = cosine_similarity([email_full], [email_minimal])[0][0]

    print(f"   'Customer Email Address' vs 'customer_email': {sim_full_short:.3f}")
    print(f"   'Customer Email Address' vs 'email': {sim_full_minimal:.3f}")

    if sim_full_short < 0.7:
        print("   ⚠️  WARNING: Similar terms have low similarity!")
        print("   Possible issues:")
        print("   - Type-aware embeddings might be adding too much noise")
        print("   - Abbreviation expansion not working")
        print("   - Model not loaded correctly")


def main():
    print("\n" + "=" * 80)
    print("MATCHING ACCURACY DIAGNOSTIC")
    print("=" * 80)

    # Check embeddings first
    check_embeddings()

    # Debug matching
    debug_single_match()

    print("\n" + "=" * 80)
    print("DIAGNOSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()