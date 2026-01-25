import json
from datetime import datetime
from io import StringIO
from pathlib import Path

import pandas as pd


def generate_csv_report(calculated_df: pd.DataFrame, output_path: str) -> str:
    """
    Generate CSV report with all trade details.

    Args:
        calculated_df: DataFrame with calculated notional values
        output_path: Path to save the CSV file

    Returns:
        Path to the saved file
    """
    # Select columns for export
    export_columns = [
        "close_time",
        "symbol",
        "type",
        "lots",
        "open_price",
        "close_price",
        "commission",
        "swap",
        "profit",
        "fx_rate",
        "fx_source",
        "notional_usd",
    ]

    export_df = calculated_df[export_columns].copy()
    export_df.to_csv(output_path, index=False)

    return output_path


def generate_csv_report_bytes(calculated_df: pd.DataFrame) -> bytes:
    """
    Generate CSV report in memory and return as bytes.

    Args:
        calculated_df: DataFrame with calculated notional values

    Returns:
        CSV content as bytes
    """
    export_columns = [
        "close_time",
        "symbol",
        "type",
        "lots",
        "open_price",
        "close_price",
        "commission",
        "swap",
        "profit",
        "fx_rate",
        "fx_source",
        "notional_usd",
    ]

    export_df = calculated_df[export_columns].copy()
    csv_buffer = StringIO()
    export_df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue().encode("utf-8")


def generate_json_report(
    calculated_df: pd.DataFrame, summary_df: pd.DataFrame, fx_summary: dict, platform_name: str, output_path: str
) -> str:
    """
    Generate JSON report with full results.

    Args:
        calculated_df: DataFrame with calculated notional values
        summary_df: DataFrame with summary by symbol
        fx_summary: Dict with FX source counts
        platform_name: Name of the detected platform
        output_path: Path to save the JSON file

    Returns:
        Path to the saved file
    """
    report = {
        "generated_at": datetime.now().isoformat(),
        "platform": platform_name,
        "summary": {
            "total_notional_usd": float(calculated_df["notional_usd"].sum()),
            "total_trades": len(calculated_df),
            "total_lots": float(calculated_df["lots"].sum()),
            "period_start": str(calculated_df["close_time"].min()),
            "period_end": str(calculated_df["close_time"].max()),
        },
        "fx_sources": fx_summary,
        "by_symbol": summary_df.to_dict(orient="records"),
        "trades": calculated_df.to_dict(orient="records"),
    }

    # Convert any non-serializable types
    def convert_types(obj):
        if isinstance(obj, pd.Timestamp | datetime):
            return obj.isoformat()
        if pd.isna(obj):
            return None
        return obj

    # Write JSON with custom encoder
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=convert_types)

    return output_path


def get_default_output_path(format_type: str = "csv") -> str:
    """Generate default output filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"notional_report_{timestamp}.{format_type}"


def format_currency(value: float) -> str:
    """Format a number as USD currency"""
    return f"${value:,.2f}"


def format_percentage(value: float) -> str:
    """Format a number as percentage"""
    return f"{value:.1f}%"


def print_console_report(
    calculated_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    fx_summary: dict,
    platform_name: str,
    filepath: str,
    auto_detected: bool = True,
    date_filter: str = None,
):
    """
    Print formatted report to console.

    Args:
        date_filter: Optional description of applied date filter (e.g., "last 7 days")
    """
    total_notional = calculated_df["notional_usd"].sum()
    total_trades = len(calculated_df)
    total_lots = calculated_df["lots"].sum()
    period_start = calculated_df["close_time"].min()
    period_end = calculated_df["close_time"].max()

    # Format dates as DD-MM-YYYY
    def format_date(dt):
        if hasattr(dt, "strftime"):
            return dt.strftime("%d-%m-%Y")
        return str(dt)

    print()
    print("=" * 70)
    print("NOTIONAL VOLUME REPORT")
    print("=" * 70)
    print(f"File: {Path(filepath).name}")
    detection_method = "(auto-detected)" if auto_detected else "(specified)"
    print(f"Platform: {platform_name} {detection_method}")
    print(f"Period: {format_date(period_start)} to {format_date(period_end)}")
    if date_filter:
        print(f"Filter: {date_filter}")
    print("-" * 70)

    # Trade details table
    print()
    print("TRADE DETAILS:")
    print(f"{'Symbol':<10} {'Lots':>8} {'Close Price':>14} {'FX Rate':>10} {'Source':>12} {'Notional (USD)':>18}")
    print("-" * 70)

    for _, trade in calculated_df.iterrows():
        print(
            f"{trade['symbol']:<10} {trade['lots']:>8.2f} {trade['close_price']:>14,.2f} "
            f"{trade['fx_rate']:>10.4f} {trade['fx_source']:>12} {format_currency(trade['notional_usd']):>18}"
        )

    # Summary by symbol
    print()
    print("SUMMARY BY SYMBOL:")
    print(f"{'Symbol':<10} {'Total Lots':>12} {'Notional (USD)':>18} {'%':>8}")
    print("-" * 50)

    for _, row in summary_df.iterrows():
        print(
            f"{row['symbol']:<10} {row['total_lots']:>12.2f} "
            f"{format_currency(row['notional_usd']):>18} {format_percentage(row['percentage']):>8}"
        )

    # FX Source summary
    print()
    print("FX RATE SOURCES:")
    if fx_summary["direct"] > 0:
        print(f"  - {fx_summary['direct']} trade(s) using direct USD quote (no conversion needed)")
    if fx_summary["api"] > 0:
        print(f"  - {fx_summary['api']} trade(s) using historical API rates (frankfurter.app)")
    if fx_summary["api_cached"] > 0:
        print(f"  - {fx_summary['api_cached']} trade(s) using cached API rates")
    if fx_summary["fallback"] > 0:
        print(f"  - {fx_summary['fallback']} trade(s) using FALLBACK rates (API unavailable)")
        print("    WARNING: Fallback rates are approximate and may affect accuracy.")

    # Grand total
    print()
    print("=" * 70)
    print(f"GRAND TOTAL: {format_currency(total_notional)} USD")
    print(f"Total Trades: {total_trades} | Total Lots: {total_lots:.2f}")
    print("=" * 70)
    print()
