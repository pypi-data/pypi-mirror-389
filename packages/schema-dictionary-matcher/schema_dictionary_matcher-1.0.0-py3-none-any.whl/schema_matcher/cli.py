"""
Command-line interface for schema-dictionary-matcher
"""
import argparse
import json
from pathlib import Path


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Schema Dictionary Matcher - Semantic schema matching"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Match command
    match_parser = subparsers.add_parser("match", help="Match Avro schema")
    match_parser.add_argument("schema", help="Path to Avro schema file")
    match_parser.add_argument("-o", "--output", help="Output JSON file")
    match_parser.add_argument("-k", "--top-k", type=int, default=5, help="Top K results")

    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync data dictionary")
    sync_parser.add_argument("excel", help="Path to Excel dictionary")
    sync_parser.add_argument("--force", action="store_true", help="Force rebuild")

    # API command
    api_parser = subparsers.add_parser("api", help="Start REST API")
    api_parser.add_argument("--host", default="0.0.0.0", help="Host address")
    api_parser.add_argument("--port", type=int, default=8000, help="Port number")

    args = parser.parse_args()

    if args.command == "match":
        from .config_production import ProductionConfig
        from .schema_matcher import AdvancedSchemaMatcher

        config = ProductionConfig()
        matcher = AdvancedSchemaMatcher(config)

        results = matcher.match_avro_schema(args.schema)

        # Format output
        output_data = [
            {
                "field": r.avro_field.full_path,
                "matched": r.matched_entry.business_name,
                "confidence": r.final_confidence,
                "decision": r.decision,
            }
            for r in results if r.rank == 1
        ]

        if args.output:
            with open(args.output, "w") as f:
                json.dump(output_data, f, indent=2)
            print(f"Results written to {args.output}")
        else:
            print(json.dumps(output_data, indent=2))

    elif args.command == "sync":
        from .config_production import ProductionConfig
        from .schema_matcher import AdvancedSchemaMatcher

        config = ProductionConfig()
        matcher = AdvancedSchemaMatcher(config)

        stats = matcher.sync_excel_to_vector_db(args.excel, force_rebuild=args.force)
        print(f"Synced {stats.total_entries} entries")
        print(f"Added: {stats.added}, Modified: {stats.modified}, Deleted: {stats.deleted}")

    elif args.command == "api":
        import uvicorn
        from .api import app

        print(f"Starting API on {args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()