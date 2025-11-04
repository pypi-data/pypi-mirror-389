"""
Update configuration to use local models instead of HuggingFace
"""

from pathlib import Path

def get_local_model_path(model_name: str) -> str:
    """Convert HuggingFace model name to local path."""
    safe_name = model_name.replace("/", "--")
    return str(Path("models") / safe_name)


def update_config():
    """Update config_production.py to use local models."""

    config_file = Path("config_production.py")

    if not config_file.exists():
        print("❌ config_production.py not found")
        return

    # Read current config
    with open(config_file, 'r') as f:
        content = f.read()

    # Replace HuggingFace model names with local paths
    replacements = {
        '"BAAI/bge-base-en-v1.5"': f'"{get_local_model_path("BAAI/bge-base-en-v1.5")}"',
        '"BAAI/bge-reranker-base"': f'"{get_local_model_path("BAAI/bge-reranker-base")}"',
        '"answerdotai/answerai-colbert-small-v1"': f'"{get_local_model_path("answerdotai/answerai-colbert-small-v1")}"',
    }

    for old, new in replacements.items():
        content = content.replace(old, new)

    # Write updated config
    with open(config_file, 'w') as f:
        f.write(content)

    print("✅ Updated config_production.py to use local models")
    print("\nUpdated paths:")
    for old, new in replacements.items():
        print(f"  {old} → {new}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("UPDATE CONFIG FOR OFFLINE MODELS")
    print("="*80)

    update_config()

    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)
    print("Check that these directories exist:")

    models = [
        "BAAI--bge-base-en-v1.5",
        "BAAI--bge-reranker-base",
        "answerdotai--answerai-colbert-small-v1"
    ]

    for model in models:
        path = Path("models") / model
        exists = "✅" if path.exists() else "❌"
        print(f"{exists} {path}")
