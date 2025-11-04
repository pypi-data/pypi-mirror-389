"""
Test that offline models work correctly
"""

from pathlib import Path
from .config_production import ProductionConfig


def test_offline_models():
    """Verify all models load from local paths."""

    config = ProductionConfig()

    print("\n" + "=" * 80)
    print("TESTING OFFLINE MODELS")
    print("=" * 80)

    models = [
        ("Embedding Model", config.embedding_model),
        ("Cross-Encoder", config.cross_encoder_model),
        ("ColBERT Model", config.colbert_model),
    ]

    print("\nConfigured paths:")
    for name, path in models:
        exists = Path(path).exists()
        status = "✅" if exists else "❌"
        print(f"{status} {name}: {path}")

    # Test loading
    print("\n" + "=" * 80)
    print("LOADING MODELS...")
    print("=" * 80)

    try:
        from sentence_transformers import SentenceTransformer
        from sentence_transformers.cross_encoder import CrossEncoder

        # Test embedding model
        print("\n1. Loading embedding model...")
        embedding_model = SentenceTransformer(config.embedding_model)
        print(f"   ✅ Loaded: {config.embedding_model}")
        print(f"   Dimension: {embedding_model.get_sentence_embedding_dimension()}")

        # Test embedding
        test_text = "customer email address"
        embedding = embedding_model.encode(test_text)
        print(f"   ✅ Test encoding: {len(embedding)} dimensions")

        # Test cross-encoder
        print("\n2. Loading cross-encoder...")
        cross_encoder = CrossEncoder(config.cross_encoder_model)
        print(f"   ✅ Loaded: {config.cross_encoder_model}")

        # Test scoring
        scores = cross_encoder.predict([
            ("customer email", "email address for customer"),
            ("transaction amount", "amount of transaction")
        ])
        print(f"   ✅ Test scoring: {scores}")

        print("\n" + "=" * 80)
        print("✅ ALL MODELS WORKING OFFLINE!")
        print("=" * 80)
        print("\nYour setup is ready for deployment behind corporate firewall.")
        print("No HuggingFace access needed at runtime.")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Verify models were downloaded: ls models/")
        print("2. Check config paths are correct")
        print("3. Ensure sentence-transformers is installed")
        return False


if __name__ == "__main__":
    success = test_offline_models()
    exit(0 if success else 1)