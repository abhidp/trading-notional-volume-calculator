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
from datetime import datetime, timedelta
from io import BytesIO
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


def parse_date(date_str: str) -> datetime:
    """Parse date string in DD-MM-YYYY format"""
    try:
        return datetime.strptime(date_str, '%d-%m-%Y')
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use DD-MM-YYYY format (e.g., 25-01-2026)")


def get_date_filter(args) -> tuple[datetime | None, datetime | None, str | None]:
    """
    Determine date filter from command line arguments.
    Returns (start_date, end_date, filter_description) or (None, None, None) if no filter.
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Check for conflicting options
    filter_options = sum([
        args.from_date is not None or args.to_date is not None,
        args.last is not None,
        args.this_month
    ])

    if filter_options > 1:
        raise ValueError("Cannot combine --from/--to with --last or --this-month. Use one filter type.")

    # Custom date range
    if args.from_date or args.to_date:
        start_date = parse_date(args.from_date) if args.from_date else None
        end_date = parse_date(args.to_date) if args.to_date else None

        if start_date and end_date and start_date > end_date:
            raise ValueError("Start date must be before or equal to end date")

        if start_date and end_date:
            desc = f"{args.from_date} to {args.to_date}"
        elif start_date:
            desc = f"from {args.from_date}"
        else:
            desc = f"until {args.to_date}"

        return start_date, end_date, desc

    # Last N days
    if args.last:
        if args.last <= 0:
            raise ValueError("--last value must be a positive number")
        start_date = today - timedelta(days=args.last - 1)
        return start_date, today, f"last {args.last} days"

    # This month
    if args.this_month:
        start_date = today.replace(day=1)
        return start_date, today, "this month"

    return None, None, None


def filter_trades_by_date(df, start_date: datetime | None, end_date: datetime | None):
    """Filter trades dataframe by date range based on close_time"""
    import pandas as pd

    if start_date is None and end_date is None:
        return df

    # Ensure close_time is datetime
    df = df.copy()
    df['close_time'] = pd.to_datetime(df['close_time'])

    # Create date-only column for comparison
    df['_close_date'] = df['close_time'].dt.normalize()

    if start_date and end_date:
        mask = (df['_close_date'] >= pd.Timestamp(start_date)) & (df['_close_date'] <= pd.Timestamp(end_date))
    elif start_date:
        mask = df['_close_date'] >= pd.Timestamp(start_date)
    else:
        mask = df['_close_date'] <= pd.Timestamp(end_date)

    filtered = df[mask].drop(columns=['_close_date'])
    return filtered


def main():
    parser = argparse.ArgumentParser(
        description="Calculate notional trading volume from trade history exports.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py trades.xlsx                    # Auto-detect platform, all trades
  python cli.py trades.xlsx --platform mt5     # Specify MT5 platform
  python cli.py trades.xlsx -o report.csv      # Export to CSV
  python cli.py trades.xlsx --format json      # Export to JSON
  python cli.py --list-platforms               # Show supported platforms

Date Filtering:
  python cli.py trades.xlsx --last 7           # Last 7 days
  python cli.py trades.xlsx --last 30          # Last 30 days
  python cli.py trades.xlsx --this-month       # Current calendar month
  python cli.py trades.xlsx --from 01-01-2026  # From specific date
  python cli.py trades.xlsx --to 31-01-2026    # Until specific date
  python cli.py trades.xlsx --from 01-01-2026 --to 15-01-2026  # Date range
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

    # Date filter arguments
    parser.add_argument(
        '--from', '-F',
        dest='from_date',
        help='Start date for filtering (DD-MM-YYYY format)'
    )

    parser.add_argument(
        '--to', '-T',
        dest='to_date',
        help='End date for filtering (DD-MM-YYYY format)'
    )

    parser.add_argument(
        '--last',
        type=int,
        metavar='DAYS',
        help='Filter to last N days (e.g., --last 7 for last week)'
    )

    parser.add_argument(
        '--this-month',
        action='store_true',
        help='Filter to current calendar month'
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
        filename = filepath.name

        # Read file into memory (same approach as web app)
        with open(filepath, 'rb') as f:
            file_data = BytesIO(f.read())

        # Get parser (auto-detect or specified)
        auto_detected = args.platform is None
        if auto_detected:
            print(f"Auto-detecting platform for: {filename}")
            trade_parser = detect_platform(file_data, filename)
        else:
            trade_parser = get_parser(args.platform)

        platform_name = trade_parser.get_platform_name()
        print(f"Platform: {platform_name}")

        # Parse trades
        print("Parsing trade history...")
        file_data.seek(0)  # Reset to beginning after detection
        trades_df = trade_parser.parse(file_data, filename)
        total_trades = len(trades_df)
        print(f"Found {total_trades} trades")

        # Apply date filter if specified
        start_date, end_date, filter_desc = get_date_filter(args)
        if filter_desc:
            print(f"Applying date filter: {filter_desc}")
            trades_df = filter_trades_by_date(trades_df, start_date, end_date)
            filtered_count = len(trades_df)
            print(f"Filtered to {filtered_count} trades (of {total_trades} total)")

            if trades_df.empty:
                print("Error: No trades found in the specified date range.", file=sys.stderr)
                return 1

        # Calculate notional values
        print("Calculating notional volumes...")
        calculated_df, skipped_symbols = calculate_notional(trades_df)

        # Show warning if any symbols were skipped
        if skipped_symbols:
            print("\n" + "=" * 60)
            print("WARNING: Skipped unsupported symbols (likely Stock CFDs):")
            for symbol, count in skipped_symbols.items():
                print(f"  - {symbol}: {count} trades")
            print("Stock CFD support coming soon. See TODO.md for details.")
            print("=" * 60 + "\n")

        if calculated_df.empty:
            print("Error: No supported trades found. All trades were skipped.", file=sys.stderr)
            return 1

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
            auto_detected=auto_detected,
            date_filter=filter_desc
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
