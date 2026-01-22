#!/usr/bin/env python3
"""
Trading Notional Volume Calculator - Web UI

Flask web application for calculating notional trading volume from trade history exports.
"""

import os
import uuid
import warnings
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
import plotly.graph_objects as go
import plotly.utils
import json

# Suppress openpyxl style warning
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

from utils.parsers import detect_platform, get_parser, list_platforms
from utils.calculator import calculate_notional, summarize_by_symbol, get_fx_source_summary
from utils.report_generator import generate_csv_report, get_default_output_path

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configuration
UPLOAD_FOLDER = Path(__file__).parent / 'uploads'
OUTPUT_FOLDER = Path(__file__).parent / 'outputs'
ALLOWED_EXTENSIONS = {'xlsx', 'csv'}

# Ensure folders exist
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

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
    """Handle file upload and process"""
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

    # Save file temporarily
    file_id = str(uuid.uuid4())
    filename = f"{file_id}_{file.filename}"
    filepath = UPLOAD_FOLDER / filename
    file.save(filepath)

    try:
        # Get parser
        if platform == 'auto':
            parser = detect_platform(str(filepath))
            auto_detected = True
        else:
            parser = get_parser(platform)
            auto_detected = False

        platform_name = parser.get_platform_name()

        # Parse trades
        trades_df = parser.parse(str(filepath))

        if trades_df.empty:
            flash('No trades found in the file', 'error')
            return redirect(url_for('index'))

        # Calculate notional values
        calculated_df = calculate_notional(trades_df)
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
                y=-0.05,
                xanchor="center",
                x=0.5
            ),
            margin=dict(t=20, b=80, l=20, r=20),
            height=400
        )
        pie_chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        # Store results
        result_id = file_id
        results_store[result_id] = {
            'platform_name': platform_name,
            'auto_detected': auto_detected,
            'filename': file.filename,
            'total_notional': total_notional,
            'total_trades': total_trades,
            'total_lots': total_lots,
            'period_start': period_start.strftime('%Y-%m-%d') if hasattr(period_start, 'strftime') else str(period_start),
            'period_end': period_end.strftime('%Y-%m-%d') if hasattr(period_end, 'strftime') else str(period_end),
            'trades': calculated_df.to_dict('records'),
            'summary': summary_df.to_dict('records'),
            'fx_summary': fx_summary,
            'pie_chart_json': pie_chart_json,
            'filepath': str(filepath),
        }

        return redirect(url_for('results', result_id=result_id))

    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')
        # Clean up uploaded file on error
        if filepath.exists():
            filepath.unlink()
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
    """Download CSV report"""
    if result_id not in results_store:
        flash('Results not found.', 'error')
        return redirect(url_for('index'))

    data = results_store[result_id]

    # Generate CSV
    import pandas as pd
    calculated_df = pd.DataFrame(data['trades'])

    output_filename = f"notional_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    output_path = OUTPUT_FOLDER / output_filename

    generate_csv_report(calculated_df, str(output_path))

    return send_file(
        output_path,
        as_attachment=True,
        download_name=output_filename,
        mimetype='text/csv'
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
