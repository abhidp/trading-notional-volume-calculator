#!/usr/bin/env python3
"""
Trading Notional Volume Calculator - CLI Tool

Calculate total notional trading volume (USD) from exported trade history reports.
Supports multiple trading platforms including MT5 and cTrader.

Usage:
    python cli.py <filepath> [--platform mt5|ctrader] [-o output.csv] [--format csv|json]
    python cli.py --list-platforms
"""

import argparse
import sys
import warnings
from pathlib import Path

# Suppress openpyxl style warning for Excel files without default styles
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

from utils.parsers import detect_platform, get_parser, list_platforms
from utils.calculator import calculate_notional, summarize_by_symbol, get_fx_source_summary
from utils.report_generator import (
    print_console_report,
    generate_csv_report,
    generate_json_report,
    get_default_output_path,
)


def validate_file(filepath: str) -> Path:
    """Validate that the file exists and has a supported format"""
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    if path.suffix.lower() not in ['.xlsx', '.csv']:
        raise ValueError(f"Unsupported file format: {path.suffix}. Supported formats: .xlsx, .csv")

    return path


def main():
    parser = argparse.ArgumentParser(
        description="Calculate notional trading volume from trade history exports.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py trades.xlsx                    # Auto-detect platform
  python cli.py trades.xlsx --platform mt5     # Specify MT5 platform
  python cli.py trades.xlsx -o report.csv      # Export to CSV
  python cli.py trades.xlsx --format json      # Export to JSON
  python cli.py --list-platforms               # Show supported platforms
        """
    )

    parser.add_argument(
        'filepath',
        nargs='?',
        help='Path to the trade history export file (.xlsx or .csv)'
    )

    parser.add_argument(
        '--platform', '-p',
        choices=['mt5', 'ctrader'],
        help='Trading platform (default: auto-detect)'
    )

    parser.add_argument(
        '--output', '-o',
        help='Output file path for the report'
    )

    parser.add_argument(
        '--format', '-f',
        choices=['csv', 'json'],
        default='csv',
        help='Output format (default: csv)'
    )

    parser.add_argument(
        '--list-platforms',
        action='store_true',
        help='List supported trading platforms'
    )

    args = parser.parse_args()

    # Handle --list-platforms
    if args.list_platforms:
        print("\nSupported Trading Platforms:")
        print("-" * 30)
        for platform in list_platforms():
            print(f"  - {platform}")
        print()
        return 0

    # Require filepath if not listing platforms
    if not args.filepath:
        parser.print_help()
        return 1

    try:
        # Validate file
        filepath = validate_file(args.filepath)

        # Get parser (auto-detect or specified)
        auto_detected = args.platform is None
        if auto_detected:
            print(f"Auto-detecting platform for: {filepath.name}")
            trade_parser = detect_platform(str(filepath))
        else:
            trade_parser = get_parser(args.platform)

        platform_name = trade_parser.get_platform_name()
        print(f"Platform: {platform_name}")

        # Parse trades
        print("Parsing trade history...")
        trades_df = trade_parser.parse(str(filepath))
        print(f"Found {len(trades_df)} trades")

        # Calculate notional values
        print("Calculating notional volumes...")
        calculated_df = calculate_notional(trades_df)

        # Generate summaries
        summary_df = summarize_by_symbol(calculated_df)
        fx_summary = get_fx_source_summary(calculated_df)

        # Print console report
        print_console_report(
            calculated_df=calculated_df,
            summary_df=summary_df,
            fx_summary=fx_summary,
            platform_name=platform_name,
            filepath=str(filepath),
            auto_detected=auto_detected
        )

        # Export to file if requested
        if args.output:
            output_path = args.output
        else:
            # Generate default output path in outputs directory
            output_dir = Path(__file__).parent / 'outputs'
            output_dir.mkdir(exist_ok=True)
            output_path = str(output_dir / get_default_output_path(args.format))

        if args.format == 'csv':
            generate_csv_report(calculated_df, output_path)
            print(f"CSV report saved to: {output_path}")
        elif args.format == 'json':
            generate_json_report(
                calculated_df=calculated_df,
                summary_df=summary_df,
                fx_summary=fx_summary,
                platform_name=platform_name,
                output_path=output_path
            )
            print(f"JSON report saved to: {output_path}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
