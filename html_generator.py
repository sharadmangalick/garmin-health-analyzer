#!/usr/bin/env python3
"""
HTML Report Generator - Creates interactive health insights HTML report from Garmin data.

Generates a modern, responsive HTML report with charts and visualizations.
"""

from datetime import datetime
from data_analyzer import GarminDataAnalyzer


def generate_insights_html(output_path: str = None, data_dir: str = "data") -> str:
    """
    Generate comprehensive insights HTML report from Garmin data.

    Args:
        output_path: Where to save the HTML. Defaults to current directory.
        data_dir: Directory containing Garmin data JSON files.

    Returns:
        Path to the generated HTML file.
    """
    # Load and analyze data
    print("Loading data...")
    analyzer = GarminDataAnalyzer(data_dir)
    load_result = analyzer.load_data()

    if load_result['daily_summaries'] == 0:
        raise ValueError("No data found. Please run 'python main.py fetch' first.")

    print(f"Analyzing {load_result['daily_summaries']} days of data...")
    results = analyzer.analyze_all()

    # Generate HTML
    html = generate_html_content(results, load_result)

    # Save HTML
    if output_path is None:
        output_path = 'Health_Insights_Report.html'

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"HTML report saved to: {output_path}")
    return output_path


def generate_html_content(results: dict, load_result: dict) -> str:
    """Generate the HTML content."""

    overview = results.get('overview', {})
    rhr = results.get('resting_hr', {})
    bb = results.get('body_battery', {})
    vo2 = results.get('vo2max', {})
    sleep = results.get('sleep', {})
    sed = results.get('sedentary', {})
    stress = results.get('stress', {})
    steps = results.get('steps', {})
    dow = results.get('day_of_week', {})
    monthly = results.get('monthly_trends', {})
    recommendations = results.get('recommendations', [])

    # Build metric cards HTML
    metric_cards = ""

    if rhr.get('available'):
        status_class = 'danger' if rhr['status'] == 'concern' else ('success' if rhr['status'] == 'good' else 'warning')
        metric_cards += f"""
        <div class="metric-card">
            <div class="metric-icon">❤️</div>
            <div class="metric-title">Resting Heart Rate</div>
            <div class="metric-value">{rhr['current']} <span class="metric-unit">bpm</span></div>
            <div class="metric-change {status_class}">{rhr['change']:+.1f} from baseline ({rhr['baseline']})</div>
            <div class="metric-detail">Trend: {rhr['trend'].title()}</div>
        </div>
        """

    if bb.get('available'):
        status_class = 'danger' if bb['status'] == 'concern' else ('success' if bb['status'] == 'good' else 'warning')
        metric_cards += f"""
        <div class="metric-card">
            <div class="metric-icon">🔋</div>
            <div class="metric-title">Body Battery</div>
            <div class="metric-value">{bb['current_wake']} <span class="metric-unit">wake</span></div>
            <div class="metric-change {status_class}">{bb['change']:+.0f} from baseline ({bb['baseline_wake']})</div>
            <div class="metric-detail">Avg recharge: +{bb['avg_recharge']}</div>
        </div>
        """

    if vo2.get('available'):
        status_class = 'success' if vo2['status'] == 'good' else ('danger' if vo2['status'] == 'concern' else 'warning')
        metric_cards += f"""
        <div class="metric-card">
            <div class="metric-icon">🫁</div>
            <div class="metric-title">VO2 Max</div>
            <div class="metric-value">{vo2['current']} <span class="metric-unit">ml/kg/min</span></div>
            <div class="metric-change {status_class}">{vo2['change']:+.1f} ({vo2['fitness_level']})</div>
            <div class="metric-detail">Range: {vo2['min']} - {vo2['max']}</div>
        </div>
        """

    if sleep.get('available'):
        status_class = 'danger' if sleep['status'] == 'concern' else ('success' if sleep['status'] == 'good' else 'warning')
        metric_cards += f"""
        <div class="metric-card">
            <div class="metric-icon">😴</div>
            <div class="metric-title">Sleep</div>
            <div class="metric-value">{sleep['avg_hours']} <span class="metric-unit">hrs avg</span></div>
            <div class="metric-change {status_class}">{sleep['under_6h_pct']}% nights under 6h</div>
            <div class="metric-detail">{sleep['nights_7plus_pct']}% nights 7+ hours</div>
        </div>
        """

    if stress.get('available'):
        status_class = 'danger' if stress['status'] == 'concern' else ('success' if stress['status'] == 'good' else 'warning')
        metric_cards += f"""
        <div class="metric-card">
            <div class="metric-icon">😰</div>
            <div class="metric-title">Stress Level</div>
            <div class="metric-value">{stress['avg']} <span class="metric-unit">avg</span></div>
            <div class="metric-change {status_class}">{stress['high_stress_pct']}% days high stress</div>
            <div class="metric-detail">Range: {stress['min']} - {stress['max']}</div>
        </div>
        """

    if steps.get('available'):
        metric_cards += f"""
        <div class="metric-card">
            <div class="metric-icon">👟</div>
            <div class="metric-title">Daily Steps</div>
            <div class="metric-value">{steps['avg']:,.0f} <span class="metric-unit">avg</span></div>
            <div class="metric-change warning">{steps['low_days_pct']}% low activity days</div>
            <div class="metric-detail">Variability: {steps['variability'].title()}</div>
        </div>
        """

    # Build recommendations HTML
    recommendations_html = ""
    for rec in recommendations:
        priority_class = rec['priority']
        recommendations_html += f"""
        <div class="recommendation {priority_class}">
            <div class="rec-header">
                <span class="rec-category">{rec['category']}</span>
                <span class="rec-priority">{rec['priority'].upper()}</span>
            </div>
            <div class="rec-finding">{rec['finding']}</div>
            <div class="rec-action">{rec['recommendation']}</div>
            <div class="rec-science">{rec['science']}</div>
        </div>
        """

    # Build sedentary correlation table
    sed_table = ""
    if sed.get('available') and sed.get('correlation_found'):
        sed_table = f"""
        <div class="data-table">
            <h3>🪑 Sedentary Time vs Sleep</h3>
            <table>
                <thead>
                    <tr>
                        <th>Sedentary Hours</th>
                        <th>Avg Sleep</th>
                        <th>Impact</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="good">
                        <td>&lt; 14 hours</td>
                        <td>{sed.get('low_sed_avg_sleep', 'N/A')}h</td>
                        <td>✓ Best sleep</td>
                    </tr>
                    <tr class="warning">
                        <td>14-17 hours</td>
                        <td>{sed.get('med_sed_avg_sleep', 'N/A')}h</td>
                        <td>~ Moderate</td>
                    </tr>
                    <tr class="danger">
                        <td>17+ hours</td>
                        <td>{sed.get('high_sed_avg_sleep', 'N/A')}h</td>
                        <td>✗ Poor sleep</td>
                    </tr>
                </tbody>
            </table>
            <p class="table-note">Key insight: Sedentary time strongly predicts sleep quality.</p>
        </div>
        """

    # Build day of week table
    dow_table = ""
    if dow.get('available'):
        dow_rows = ""
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            data = dow['by_day'].get(day, {})
            sleep_val = f"{data.get('avg_sleep', '-')}h" if data.get('avg_sleep') else '-'
            bb_val = str(int(data.get('avg_bb', 0))) if data.get('avg_bb') else '-'
            stress_val = str(int(data.get('avg_stress', 0))) if data.get('avg_stress') else '-'
            steps_val = f"{data.get('avg_steps', 0):,.0f}" if data.get('avg_steps') else '-'

            row_class = ""
            if day == dow.get('best_sleep_day'):
                row_class = "good"
            elif day == dow.get('worst_sleep_day'):
                row_class = "danger"

            dow_rows += f"""
                <tr class="{row_class}">
                    <td>{day[:3]}</td>
                    <td>{sleep_val}</td>
                    <td>{bb_val}</td>
                    <td>{stress_val}</td>
                    <td>{steps_val}</td>
                </tr>
            """

        dow_table = f"""
        <div class="data-table">
            <h3>📅 Day of Week Patterns</h3>
            <table>
                <thead>
                    <tr>
                        <th>Day</th>
                        <th>Sleep</th>
                        <th>Body Battery</th>
                        <th>Stress</th>
                        <th>Steps</th>
                    </tr>
                </thead>
                <tbody>
                    {dow_rows}
                </tbody>
            </table>
            <p class="table-note">Best sleep: {dow.get('best_sleep_day', 'N/A')} | Worst: {dow.get('worst_sleep_day', 'N/A')}</p>
        </div>
        """

    # Build monthly trends table
    monthly_table = ""
    if monthly.get('available') and monthly.get('by_month'):
        monthly_rows = ""
        for month, data in monthly['by_month'].items():
            try:
                month_display = datetime.strptime(month, '%Y-%m').strftime('%b %Y')
            except:
                month_display = month

            rhr_val = str(data.get('avg_rhr', '-')) if data.get('avg_rhr') else '-'
            bb_val = str(int(data.get('avg_bb', 0))) if data.get('avg_bb') else '-'
            sleep_val = f"{data.get('avg_sleep', '-')}h" if data.get('avg_sleep') else '-'
            stress_val = str(int(data.get('avg_stress', 0))) if data.get('avg_stress') else '-'
            vig_val = str(int(data.get('total_vigorous', 0))) if data.get('total_vigorous') else '-'

            monthly_rows += f"""
                <tr>
                    <td>{month_display}</td>
                    <td>{rhr_val}</td>
                    <td>{bb_val}</td>
                    <td>{sleep_val}</td>
                    <td>{stress_val}</td>
                    <td>{vig_val}</td>
                </tr>
            """

        monthly_table = f"""
        <div class="data-table full-width">
            <h3>📈 Monthly Trends</h3>
            <table>
                <thead>
                    <tr>
                        <th>Month</th>
                        <th>RHR</th>
                        <th>Body Battery</th>
                        <th>Sleep</th>
                        <th>Stress</th>
                        <th>Vigorous Min</th>
                    </tr>
                </thead>
                <tbody>
                    {monthly_rows}
                </tbody>
            </table>
        </div>
        """

    # Build stress vs recovery table
    stress_table = ""
    if stress.get('available') and stress.get('low_stress_recharge'):
        stress_table = f"""
        <div class="data-table">
            <h3>😰 Stress vs Recovery</h3>
            <table>
                <thead>
                    <tr>
                        <th>Stress Level</th>
                        <th>Overnight Recharge</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="good">
                        <td>Low (&lt;30)</td>
                        <td>+{stress.get('low_stress_recharge', 'N/A')} BB</td>
                    </tr>
                    <tr class="warning">
                        <td>Medium (30-45)</td>
                        <td>+{stress.get('med_stress_recharge', 'N/A')} BB</td>
                    </tr>
                    <tr class="danger">
                        <td>High (&gt;45)</td>
                        <td>+{stress.get('high_stress_recharge', 'N/A')} BB</td>
                    </tr>
                </tbody>
            </table>
            <p class="table-note">Stress throttles recovery more than sleep duration.</p>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Health Insights Report</title>
    <style>
        :root {{
            --primary: #4a90d9;
            --success: #28a745;
            --warning: #ffc107;
            --danger: #dc3545;
            --dark: #343a40;
            --light: #f8f9fa;
            --gray: #6c757d;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: var(--dark);
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            color: white;
            padding: 40px 20px;
        }}

        header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        header p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}

        .summary-box {{
            background: white;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}

        .summary-box h2 {{
            color: var(--primary);
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }}

        .metric-card {{
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.2s;
        }}

        .metric-card:hover {{
            transform: translateY(-4px);
        }}

        .metric-icon {{
            font-size: 2.5rem;
            margin-bottom: 12px;
        }}

        .metric-title {{
            font-size: 0.9rem;
            color: var(--gray);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}

        .metric-value {{
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--dark);
        }}

        .metric-unit {{
            font-size: 1rem;
            font-weight: normal;
            color: var(--gray);
        }}

        .metric-change {{
            font-size: 0.95rem;
            margin-top: 8px;
            padding: 4px 12px;
            border-radius: 20px;
            display: inline-block;
        }}

        .metric-change.success {{ background: #d4edda; color: #155724; }}
        .metric-change.warning {{ background: #fff3cd; color: #856404; }}
        .metric-change.danger {{ background: #f8d7da; color: #721c24; }}

        .metric-detail {{
            font-size: 0.85rem;
            color: var(--gray);
            margin-top: 8px;
        }}

        .section {{
            background: white;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}

        .section h2 {{
            color: var(--primary);
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--light);
        }}

        .recommendations {{
            display: grid;
            gap: 16px;
        }}

        .recommendation {{
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid;
        }}

        .recommendation.high {{
            background: #fff5f5;
            border-color: var(--danger);
        }}

        .recommendation.medium {{
            background: #fffbeb;
            border-color: var(--warning);
        }}

        .recommendation.low {{
            background: #f0fdf4;
            border-color: var(--success);
        }}

        .rec-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}

        .rec-category {{
            font-weight: bold;
            color: var(--dark);
        }}

        .rec-priority {{
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 4px;
            background: var(--dark);
            color: white;
        }}

        .rec-finding {{
            color: var(--gray);
            margin-bottom: 8px;
        }}

        .rec-action {{
            font-weight: 500;
            margin-bottom: 8px;
        }}

        .rec-science {{
            font-size: 0.85rem;
            color: var(--gray);
            font-style: italic;
        }}

        .data-tables {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 24px;
        }}

        .data-table {{
            background: var(--light);
            border-radius: 12px;
            padding: 20px;
        }}

        .data-table.full-width {{
            grid-column: 1 / -1;
        }}

        .data-table h3 {{
            color: var(--dark);
            margin-bottom: 16px;
            font-size: 1.1rem;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
        }}

        th, td {{
            padding: 12px;
            text-align: center;
            border-bottom: 1px solid var(--light);
        }}

        th {{
            background: var(--primary);
            color: white;
            font-weight: 500;
            font-size: 0.85rem;
        }}

        tr.good {{ background: #d4edda; }}
        tr.warning {{ background: #fff3cd; }}
        tr.danger {{ background: #f8d7da; }}

        .table-note {{
            margin-top: 12px;
            font-size: 0.85rem;
            color: var(--gray);
            font-style: italic;
        }}

        footer {{
            text-align: center;
            color: white;
            padding: 40px 20px;
            opacity: 0.9;
        }}

        footer a {{
            color: white;
        }}

        @media (max-width: 768px) {{
            header h1 {{
                font-size: 1.8rem;
            }}

            .metrics-grid {{
                grid-template-columns: 1fr;
            }}

            .data-tables {{
                grid-template-columns: 1fr;
            }}
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}

            .metric-card, .section {{
                box-shadow: none;
                border: 1px solid #ddd;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏃‍♂️ Health Insights Report</h1>
            <p>{overview.get('total_days', 0)} days analyzed | {overview.get('start_date', '')} to {overview.get('end_date', '')}</p>
            <p>Generated {datetime.now().strftime('%B %d, %Y')}</p>
        </header>

        <div class="metrics-grid">
            {metric_cards}
        </div>

        <div class="section">
            <h2>📋 Recommendations</h2>
            <div class="recommendations">
                {recommendations_html if recommendations_html else '<p>No specific recommendations at this time. Keep up the good work!</p>'}
            </div>
        </div>

        <div class="section">
            <h2>📊 Patterns & Correlations</h2>
            <div class="data-tables">
                {sed_table}
                {stress_table}
                {dow_table}
                {monthly_table}
            </div>
        </div>

        <div class="section">
            <h2>📚 The Science</h2>
            <ul style="line-height: 2; padding-left: 20px;">
                <li><strong>Sleep & Injury Risk:</strong> Less than 7 hours sleep = 1.7x injury increase</li>
                <li><strong>HRV & Recovery:</strong> Rising resting HR often indicates accumulated fatigue</li>
                <li><strong>VO2 Max:</strong> Higher values indicate better cardiovascular fitness</li>
                <li><strong>Sedentary Behavior:</strong> Prolonged sitting has health effects independent of exercise</li>
                <li><strong>Stress & Recovery:</strong> High stress throttles overnight recovery capacity</li>
            </ul>
        </div>

        <footer>
            <p>Generated by <a href="https://github.com/sharadmangalick/garmin-health-analyzer">Garmin Health Analyzer</a></p>
            <p style="margin-top: 10px; font-size: 0.85rem;">
                This report is for informational purposes only. Consult healthcare professionals for medical advice.
            </p>
        </footer>
    </div>
</body>
</html>
"""

    return html


def main():
    """Generate HTML report from data in the default directory."""
    try:
        generate_insights_html()
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
