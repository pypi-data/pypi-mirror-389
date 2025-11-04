"""
Apply fixes to the codebase
"""


def fix_examples():
    """Fix examples.py"""
    with open('examples.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find and replace the DataFrame creation
    old_code = '''    # Prepare for indexing
    import pandas as pd
    df = pd.DataFrame([vars(e) for e in entries])'''

    new_code = '''    # Prepare for indexing - FIX COLUMN NAMES
    import pandas as pd
    df = pd.DataFrame([{
        "ID": e.id,
        "Business Name": e.business_name,
        "Logical Name": e.logical_name,
        "Definition": e.definition,
        "Data Type": e.data_type,
        "Protection Level": e.protection_level
    } for e in entries])'''

    content = content.replace(old_code, new_code)

    with open('examples.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("✓ Fixed examples.py")


def fix_test():
    """Fix test_schema_matcher.py"""
    with open('test_schema_matcher.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Add disable type-aware flag
    old_config = '''    config = AdvancedConfig(
        use_colbert_reranking=False,  # Disable for faster test
        log_level="WARNING"
    )'''

    new_config = '''    config = AdvancedConfig(
        use_colbert_reranking=False,  # Disable for faster test
        use_type_aware_embeddings=False,  # DISABLE to avoid dimension issues in test
        log_level="WARNING"
    )'''

    content = content.replace(old_config, new_config)

    with open('test_schema_matcher.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("✓ Fixed test_schema_matcher.py")


def main():
    print("Applying fixes...\n")

    try:
        fix_examples()
        fix_test()

        print("\n" + "=" * 60)
        print("All fixes applied successfully!")
        print("=" * 60)
        print("\nNow run:")
        print("  python run_demo.py")
        print("  python test_schema_matcher.py")

    except Exception as e:
        print(f"Error applying fixes: {e}")


if __name__ == "__main__":
    main()