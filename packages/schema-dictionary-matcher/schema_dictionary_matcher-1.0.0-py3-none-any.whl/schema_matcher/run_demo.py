"""
Quick demo script to test the schema matcher
"""

import logging
from pathlib import Path
import sys

from .config import AdvancedConfig
from examples import create_sample_data, example_basic_usage


def main():
    """Run a quick demo."""
    print("\n" + "=" * 80)
    print("ADVANCED SCHEMA MATCHER - QUICK DEMO")
    print("=" * 80)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    try:
        # Run basic example
        example_basic_usage()

        print("\n" + "=" * 80)
        print("DEMO COMPLETE!")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Review results in ./data/match_results.json")
        print("2. Check logs in ./logs/")
        print("3. Run full examples: python examples.py")
        print("4. Run tests: python test_schema_matcher.py")

        return 0

    except Exception as e:
        print(f"\nDemo failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure all dependencies are installed: pip install -r requirements.txt")
        print("2. Check that you have sufficient disk space")
        print("3. Review logs in ./logs/ for detailed error messages")

        return 1


if __name__ == "__main__":
    sys.exit(main())