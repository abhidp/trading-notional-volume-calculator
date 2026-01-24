#!/usr/bin/env python3
"""
Trading Notional Volume Calculator - Web UI

Flask web application for calculating notional trading volume from trade history exports.
All processing is done in memory - no user data is stored on the server.
"""

import os
import uuid
import warnings
from datetime import datetime
from io import BytesIO

from flask import Flask, render_template, request, redirect, url_for, flash, Response, jsonify
import plotly.graph_objects as go
import plotly.utils
import json

# Suppress openpyxl style warning
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

from utils.parsers import detect_platform, get_parser, list_platforms
from utils.calculator import calculate_notional, summarize_by_symbol, get_fx_source_summary
from utils.report_generator import generate_csv_report_bytes

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configuration
ALLOWED_EXTENSIONS = {'xlsx', 'csv'}
MAX_RESULTS = 5  # Keep only last 5 results to limit memory usage

# Store results in memory (in production, use a database or cache)
results_store = {}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Home page with upload form"""
    platforms = list_platforms()
    return render_template('index.html', platforms=platforms)


@app.route('/upload', methods=['POST'])
def upload():
    """Handle file upload and process entirely in memory"""
    # Check if file was uploaded
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index'))

    file = request.files['file']

    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))

    if not allowed_file(file.filename):
        flash('Invalid file type. Please upload .xlsx or .csv files.', 'error')
        return redirect(url_for('index'))

    # Get selected platform
    platform = request.form.get('platform', 'auto')

    # Read file into memory (no disk storage)
    file_data = BytesIO(file.read())
    filename = file.filename

    try:
        # Get parser
        if platform == 'auto':
            parser = detect_platform(file_data, filename)
            auto_detected = True
        else:
            parser = get_parser(platform)
            auto_detected = False

        platform_name = parser.get_platform_name()

        # Parse trades (from memory)
        trades_df = parser.parse(file_data, filename)

        if trades_df.empty:
            flash('No trades found in the file', 'error')
            return redirect(url_for('index'))

        # Calculate notional values
        calculated_df, skipped_symbols = calculate_notional(trades_df)

        # Show warning if any symbols were skipped
        if skipped_symbols:
            skipped_list = [f"{symbol} ({count} trades)" for symbol, count in skipped_symbols.items()]
            flash(
                f"Skipped unsupported symbols (likely Stock CFDs): {', '.join(skipped_list)}. "
                "Stock CFD support coming soon.",
                'warning'
            )

        if calculated_df.empty:
            flash('No supported trades found in the file. All trades were skipped.', 'error')
            return redirect(url_for('index'))

        summary_df = summarize_by_symbol(calculated_df)
        fx_summary = get_fx_source_summary(calculated_df)

        # Generate results
        total_notional = calculated_df['notional_usd'].sum()
        total_trades = len(calculated_df)
        total_lots = calculated_df['lots'].sum()
        period_start = calculated_df['close_time'].min()
        period_end = calculated_df['close_time'].max()

        # Create pie chart using graph_objects for explicit control
        pie_values = [float(v) for v in summary_df['notional_usd'].tolist()]
        pie_labels = summary_df['symbol'].tolist()
        num_symbols = len(pie_labels)

        # Calculate dynamic height based on number of legend items
        # Base height for chart + extra rows for legends (4 items per row approx)
        legend_rows = (num_symbols + 3) // 4  # ceiling division
        legend_height = legend_rows * 22
        chart_height = 450 + legend_height  # Larger base height for bigger pie

        fig = go.Figure(data=[go.Pie(
            labels=pie_labels,
            values=pie_values,
            hole=0.4,
            textposition='inside',
            textinfo='percent+label'
        )])
        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.12,  # More gap between chart and legends
                xanchor="center",
                x=0.5
            ),
            margin=dict(t=10, b=legend_height + 30, l=10, r=10),  # Extra bottom margin for gap
            height=chart_height
        )
        pie_chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        # Clean up old results if limit reached
        while len(results_store) >= MAX_RESULTS:
            oldest_key = next(iter(results_store))
            del results_store[oldest_key]

        # Store results in memory (no file references)
        result_id = str(uuid.uuid4())
        results_store[result_id] = {
            'platform_name': platform_name,
            'auto_detected': auto_detected,
            'filename': filename,
            'total_notional': total_notional,
            'total_trades': total_trades,
            'total_lots': total_lots,
            'period_start': period_start.strftime('%Y-%m-%d') if hasattr(period_start, 'strftime') else str(period_start),
            'period_end': period_end.strftime('%Y-%m-%d') if hasattr(period_end, 'strftime') else str(period_end),
            'trades': calculated_df.to_dict('records'),
            'summary': summary_df.to_dict('records'),
            'fx_summary': fx_summary,
            'pie_chart_json': pie_chart_json,
        }

        return redirect(url_for('results', result_id=result_id))

    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/results/<result_id>')
def results(result_id):
    """Display calculation results"""
    if result_id not in results_store:
        flash('Results not found. Please upload a file again.', 'error')
        return redirect(url_for('index'))

    data = results_store[result_id]
    return render_template('results.html', data=data, result_id=result_id)


@app.route('/download/<result_id>')
def download(result_id):
    """Download CSV report (generated in memory)"""
    if result_id not in results_store:
        flash('Results not found.', 'error')
        return redirect(url_for('index'))

    data = results_store[result_id]

    # Generate CSV in memory
    import pandas as pd
    calculated_df = pd.DataFrame(data['trades'])
    csv_bytes = generate_csv_report_bytes(calculated_df)

    output_filename = f"notional_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        csv_bytes,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={output_filename}'}
    )


@app.route('/export/<result_id>/html')
def export_html(result_id):
    """Export report as self-contained HTML with embedded chart"""
    if result_id not in results_store:
        flash('Results not found.', 'error')
        return redirect(url_for('index'))

    data = results_store[result_id]

    # Render export template with chart JSON for client-side rendering
    html_content = render_template(
        'export.html',
        data=data,
        chart_json=data['pie_chart_json'],
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

    filename = f"notional_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    return Response(
        html_content,
        mimetype='text/html',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@app.route('/api/platforms')
def api_platforms():
    """API endpoint to list supported platforms"""
    return jsonify({'platforms': list_platforms()})


@app.template_filter('currency')
def currency_filter(value):
    """Format value as USD currency"""
    try:
        return f"${value:,.2f}"
    except (ValueError, TypeError):
        return value


@app.template_filter('percentage')
def percentage_filter(value):
    """Format value as percentage"""
    try:
        return f"{value:.1f}%"
    except (ValueError, TypeError):
        return value


@app.template_filter('datetime')
def datetime_filter(value):
    """Format datetime value"""
    try:
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return str(value)[:19]
    except (ValueError, TypeError):
        return value


@app.route('/help')
def help_page():
    """Documentation page"""
    return render_template('help.html')


if __name__ == '__main__':
    app.run(debug=True, port=5001)
