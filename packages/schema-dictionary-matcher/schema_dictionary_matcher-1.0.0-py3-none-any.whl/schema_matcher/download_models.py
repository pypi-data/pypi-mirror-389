"""
Download all required models for offline use
Run this on a machine with HuggingFace access, then commit to GitHub
"""

import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sentence_transformers.cross_encoder import CrossEncoder
import torch

# Model directory
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)


def download_model(model_name: str, model_type: str = "sentence_transformer"):
    """Download a model and save locally."""
    print(f"\n{'=' * 80}")
    print(f"Downloading: {model_name}")
    print(f"Type: {model_type}")
    print(f"{'=' * 80}")

    # Clean model name for directory
    safe_name = model_name.replace("/", "--")
    model_path = MODELS_DIR / safe_name

    try:
        if model_type == "sentence_transformer":
            model = SentenceTransformer(model_name)
            model.save(str(model_path))
            print(f"✅ Saved to: {model_path}")

        elif model_type == "cross_encoder":
            model = CrossEncoder(model_name)
            model.save(str(model_path))
            print(f"✅ Saved to: {model_path}")

        # Get model size
        total_size = sum(
            f.stat().st_size for f in model_path.rglob('*') if f.is_file()
        )
        print(f"📦 Size: {total_size / (1024 * 1024):.1f} MB")

        return True

    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def main():
    """Download all required models."""
    print("\n" + "=" * 80)
    print("MODEL DOWNLOADER FOR OFFLINE DEPLOYMENT")
    print("=" * 80)
    print("\nThis will download ~1.5GB of models")
    print("Ensure you have sufficient disk space and internet connection")
    print("=" * 80)

    models = [
        # Embedding model
        {
            "name": "BAAI/bge-base-en-v1.5",
            "type": "sentence_transformer",
            "description": "Main embedding model (420MB)"
        },
        # Cross-encoder for reranking
        {
            "name": "BAAI/bge-reranker-base",
            "type": "cross_encoder",
            "description": "Cross-encoder reranker (1GB)"
        },
        # ColBERT model (optional)
        {
            "name": "answerdotai/answerai-colbert-small-v1",
            "type": "sentence_transformer",
            "description": "ColBERT reranker (optional, 420MB)"
        }
    ]

    results = {}

    for model in models:
        print(f"\n{model['description']}")
        input("Press Enter to download (or Ctrl+C to skip)...")

        success = download_model(model["name"], model["type"])
        results[model["name"]] = success

    # Summary
    print("\n" + "=" * 80)
    print("DOWNLOAD SUMMARY")
    print("=" * 80)

    for model_name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status}: {model_name}")

    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("1. Add models/ directory to .gitattributes:")
    print("   models/**/*.bin filter=lfs diff=lfs merge=lfs -text")
    print("   models/**/*.safetensors filter=lfs diff=lfs merge=lfs -text")
    print("")
    print("2. Initialize Git LFS:")
    print("   git lfs install")
    print("   git lfs track 'models/**/*.bin'")
    print("   git lfs track 'models/**/*.safetensors'")
    print("")
    print("3. Commit models:")
    print("   git add models/")
    print("   git add .gitattributes")
    print("   git commit -m 'Add offline models'")
    print("   git push")
    print("")
    print("4. Update config to use local models (see update_config_for_offline.py)")
    print("=" * 80)


if __name__ == "__main__":
    main()