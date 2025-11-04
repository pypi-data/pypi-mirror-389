"""
RyoFaker CLI - Command-Line Interface
======================================

Command-line tool for RyoFaker data generation.

Usage:
    ryofaker --help
    ryofaker generate --schema schema.json --rows 1000 --output data.csv
    ryofaker providers --list
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from ryofaker import RyoFaker, VERSION
from ryofaker.exceptions import RyoFakerException


def execute_from_command_line(argv: Optional[List[str]] = None) -> None:
    """
    Main CLI entry point.
    
    Args:
        argv: Command-line arguments (defaults to sys.argv)
    """
    parser = create_parser()
    args = parser.parse_args(argv or sys.argv[1:])
    
    try:
        # Execute command
        if hasattr(args, "func"):
            args.func(args)
        else:
            parser.print_help()
    except RyoFakerException as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI."""
    parser = argparse.ArgumentParser(
        prog="ryofaker",
        description="RyoFaker - Enterprise data generation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"RyoFaker {VERSION}",
    )
    
    subparsers = parser.add_subparsers(title="commands", dest="command")
    
    # Generate command
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate data from schema",
    )
    generate_parser.add_argument(
        "--schema",
        required=True,
        help="Path to schema file (JSON or YAML)",
    )
    generate_parser.add_argument(
        "--rows",
        type=int,
        help="Number of rows to generate (overrides schema)",
    )
    generate_parser.add_argument(
        "--output",
        help="Output file path",
    )
    generate_parser.add_argument(
        "--format",
        default="csv",
        choices=["csv", "json", "parquet", "sql"],
        help="Output format (default: csv)",
    )
    generate_parser.add_argument(
        "--locale",
        default="en_US",
        help="Locale for data generation (default: en_US)",
    )
    generate_parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducibility",
    )
    generate_parser.set_defaults(func=generate_command)
    
    # Providers command
    providers_parser = subparsers.add_parser(
        "providers",
        help="List available providers",
    )
    providers_parser.add_argument(
        "--list",
        action="store_true",
        help="List all providers",
    )
    providers_parser.add_argument(
        "--custom",
        action="store_true",
        help="Show only custom RyoFaker providers",
    )
    providers_parser.set_defaults(func=providers_command)
    
    return parser


def generate_command(args: argparse.Namespace) -> None:
    """Execute generate command."""
    print(f"Generating data from schema: {args.schema}")
    
    # Validate schema file exists
    schema_path = Path(args.schema)
    if not schema_path.exists():
        raise RyoFakerException(f"Schema file not found: {args.schema}")
    
    # Create RyoFaker instance
    rf = RyoFaker(locale=args.locale)
    
    # Set seed if provided
    if args.seed is not None:
        rf.seed_instance(args.seed)
        print(f"Using seed: {args.seed}")
    
    # Generate data
    print(f"Generating {args.rows or 'default'} rows...")
    data = rf.from_schema(
        schema_path=str(schema_path),
        rows=args.rows,
        format=args.format,
        output=args.output,
    )
    
    # Output result
    if args.output:
        print(f"Data written to: {args.output}")
    else:
        print(f"Generated {len(data)} tables")
        for table_name, table_data in data.items():
            print(f"  - {table_name}: {len(table_data)} rows")


def providers_command(args: argparse.Namespace) -> None:
    """Execute providers command."""
    print("Available RyoFaker Providers:")
    print()
    
    if args.custom:
        providers = [
            ("india_identity", "PAN, Aadhaar, GSTIN, IFSC"),
            ("telecom", "IMEI, IMSI, MSISDN"),
            ("healthcare", "MRN, Insurance ID, ICD-10"),
            ("retail", "SKU, UPC, Order ID"),
            ("banking", "Account Number, Transaction ID, SWIFT"),
            ("edge_cases", "Boundary values, SQL injection strings"),
            ("stress", "Large blobs, deep JSON"),
        ]
    else:
        providers = [
            ("Standard Faker", "All standard Faker providers"),
            ("india_identity", "Indian identity documents"),
            ("telecom", "Telecom identifiers"),
            ("healthcare", "Healthcare identifiers"),
            ("retail", "Retail identifiers"),
            ("banking", "Banking identifiers"),
        ]
    
    for name, description in providers:
        print(f"  {name:20} - {description}")


if __name__ == "__main__":
    execute_from_command_line()
