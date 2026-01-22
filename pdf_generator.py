#!/usr/bin/env python3
"""
PDF Report Generator - Creates health insights PDF from Garmin data analysis.

Uses the GarminDataAnalyzer to process data and generates a comprehensive
PDF report with findings, recommendations, and supporting evidence.
"""

from fpdf import FPDF
from datetime import datetime
from data_analyzer import GarminDataAnalyzer


class InsightsPDF(FPDF):
    """Custom PDF class with header/footer and helper methods."""

    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, 'Garmin Health Insights Report', align='C')
            self.ln(5)

    def footer(self):
        self.set_y(-10)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()} | Generated {datetime.now().strftime("%B %d, %Y")}', align='C')

    def section_header(self, title, color=(70, 130, 180)):
        self.set_font('Helvetica', 'B', 12)
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.cell(0, 7, f' {title}', ln=True, fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def subsection(self, title):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(70, 130, 180)
        self.cell(0, 6, title, ln=True)
        self.set_text_color(0, 0, 0)

    def bullet(self, text):
        self.set_font('Helvetica', '', 9)
        self.cell(0, 5, '- ' + text, ln=True)

    def key_value(self, key, value, key_width=50):
        self.set_font('Helvetica', 'B', 9)
        self.cell(key_width, 5, key + ':', 0, 0)
        self.set_font('Helvetica', '', 9)
        self.cell(0, 5, str(value), ln=True)


def generate_insights_pdf(output_path: str = None, data_dir: str = "data") -> str:
    """
    Generate comprehensive insights PDF from Garmin data.

    Args:
        output_path: Where to save the PDF. Defaults to current directory.
        data_dir: Directory containing Garmin data JSON files.

    Returns:
        Path to the generated PDF file.
    """
    # Load and analyze data
    print("Loading data...")
    analyzer = GarminDataAnalyzer(data_dir)
    load_result = analyzer.load_data()

    if load_result['daily_summaries'] == 0:
        raise ValueError("No data found. Please run 'python main.py fetch' first.")

    print(f"Analyzing {load_result['daily_summaries']} days of data...")
    results = analyzer.analyze_all()

    # Create PDF
    pdf = InsightsPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(12, 12, 12)

    # ============ TITLE PAGE ============
    pdf.add_page()
    pdf.ln(25)

    pdf.set_font('Helvetica', 'B', 26)
    pdf.set_text_color(70, 130, 180)
    pdf.cell(0, 15, 'Health & Training Insights', ln=True, align='C')

    pdf.set_font('Helvetica', '', 14)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, 'Garmin Data Analysis Report', ln=True, align='C')

    overview = results.get('overview', {})
    if overview.get('start_date') and overview.get('end_date'):
        start = datetime.strptime(overview['start_date'], '%Y-%m-%d').strftime('%B %Y')
        end = datetime.strptime(overview['end_date'], '%Y-%m-%d').strftime('%B %Y')
        pdf.cell(0, 8, f'{start} - {end}', ln=True, align='C')

    pdf.ln(10)

    # Summary stats box
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.set_x(40)
    pdf.cell(130, 8, f"{overview.get('total_days', 0)} days of data analyzed", ln=True, align='C', fill=True)

    pdf.ln(15)

    # Executive summary
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'Executive Summary', ln=True)
    pdf.set_font('Helvetica', '', 10)

    # Build dynamic executive summary
    summary_points = []

    rhr = results.get('resting_hr', {})
    if rhr.get('available') and rhr.get('status') == 'concern':
        summary_points.append(
            f"RECOVERY SIGNAL: Your resting heart rate has risen from {rhr['baseline']} to {rhr['current']} bpm "
            f"({rhr['change']:+.1f} change), which often indicates accumulated fatigue."
        )

    bb = results.get('body_battery', {})
    if bb.get('available') and bb.get('change', 0) < -5:
        summary_points.append(
            f"ENERGY DEFICIT: Body Battery wake values have dropped from {bb['baseline_wake']} to {bb['current_wake']} "
            f"({bb['change']:+.0f} points), suggesting recovery is being outpaced by stress."
        )

    sed = results.get('sedentary', {})
    if sed.get('available') and sed.get('correlation_found'):
        summary_points.append(
            f"LIFESTYLE PATTERN: Days with 17+ hours sedentary average only {sed['high_sed_avg_sleep']}h sleep, "
            f"vs {sed['low_sed_avg_sleep']}h on more active days. Sedentary time strongly predicts sleep quality."
        )

    stress = results.get('stress', {})
    if stress.get('available') and stress.get('low_stress_recharge') and stress.get('high_stress_recharge'):
        diff = stress['low_stress_recharge'] - stress['high_stress_recharge']
        if diff > 20:
            summary_points.append(
                f"STRESS IMPACT: Low-stress nights show +{stress['low_stress_recharge']} Body Battery recharge vs "
                f"+{stress['high_stress_recharge']} on high-stress nights. Stress management may matter more than sleep duration."
            )

    vo2 = results.get('vo2max', {})
    if vo2.get('available'):
        if vo2.get('change', 0) > 1:
            summary_points.append(
                f"FITNESS GAINS: Your VO2 max has improved from {vo2['baseline']} to {vo2['current']} ml/kg/min "
                f"({vo2['change']:+.1f}), indicating improved cardiovascular fitness."
            )
        elif vo2.get('change', 0) < -1:
            summary_points.append(
                f"FITNESS ALERT: Your VO2 max has dropped from {vo2['baseline']} to {vo2['current']} ml/kg/min "
                f"({vo2['change']:+.1f}). Consider adding more aerobic training."
            )

    if not summary_points:
        summary_points.append(
            "Your metrics appear relatively stable. Review the detailed analysis below for specific patterns and opportunities."
        )

    for point in summary_points:
        pdf.multi_cell(0, 5, point)
        pdf.ln(2)

    # ============ KEY METRICS PAGE ============
    pdf.add_page()
    pdf.section_header('PART 1: KEY METRICS')

    # Resting Heart Rate
    if rhr.get('available'):
        pdf.subsection('Resting Heart Rate')
        pdf.set_font('Helvetica', '', 9)

        pdf.key_value('Baseline (first 2 weeks)', f"{rhr['baseline']} bpm")
        pdf.key_value('Current (last 2 weeks)', f"{rhr['current']} bpm")
        pdf.key_value('Change', f"{rhr['change']:+.1f} bpm ({rhr['change_pct']:+.1f}%)")
        pdf.key_value('Range', f"{rhr['min']} - {rhr['max']} bpm")
        pdf.key_value('Trend', rhr['trend'].title())

        if rhr['status'] == 'concern':
            pdf.ln(2)
            pdf.set_font('Helvetica', 'I', 8)
            pdf.multi_cell(0, 4,
                'Note: A rise of 3-5 bpm typically indicates accumulated fatigue. '
                'Consider a recovery period to allow your body to absorb recent training.')
        pdf.ln(4)

    # Body Battery
    if bb.get('available'):
        pdf.subsection('Body Battery')
        pdf.set_font('Helvetica', '', 9)

        pdf.key_value('Baseline wake value', f"{bb['baseline_wake']}")
        pdf.key_value('Current wake value', f"{bb['current_wake']}")
        pdf.key_value('Change', f"{bb['change']:+.0f} points")
        pdf.key_value('Avg overnight recharge', f"+{bb['avg_recharge']} points")
        pdf.key_value('Range', f"{bb['min_wake']} - {bb['max_wake']}")

        if bb['status'] == 'concern':
            pdf.ln(2)
            pdf.set_font('Helvetica', 'I', 8)
            pdf.multi_cell(0, 4,
                'Note: Waking below 60 suggests chronic recovery deficit. '
                'Focus on sleep quality and stress reduction.')
        pdf.ln(4)

    # VO2 Max
    vo2 = results.get('vo2max', {})
    if vo2.get('available'):
        pdf.subsection('VO2 Max')
        pdf.set_font('Helvetica', '', 9)

        pdf.key_value('Baseline', f"{vo2['baseline']} ml/kg/min")
        pdf.key_value('Current', f"{vo2['current']} ml/kg/min")
        pdf.key_value('Change', f"{vo2['change']:+.1f} ml/kg/min")
        pdf.key_value('Range', f"{vo2['min']} - {vo2['max']} ml/kg/min")
        pdf.key_value('Fitness Level', vo2['fitness_level'])
        pdf.key_value('Trend', vo2['trend'].title())

        pdf.ln(2)
        pdf.set_font('Helvetica', 'I', 8)
        pdf.multi_cell(0, 4,
            'Note: VO2 max measures your cardiovascular fitness. Higher values indicate '
            'better aerobic capacity. Improvements typically come from consistent endurance training.')
        pdf.ln(4)

    # Sleep
    sleep = results.get('sleep', {})
    if sleep.get('available'):
        pdf.subsection('Sleep')
        pdf.set_font('Helvetica', '', 9)

        pdf.key_value('Average duration', f"{sleep['avg_hours']} hours")
        pdf.key_value('Range', f"{sleep['min_hours']} - {sleep['max_hours']} hours")
        pdf.key_value('Nights under 6 hours', f"{sleep['under_6h_nights']} ({sleep['under_6h_pct']}%)")
        pdf.key_value('Nights 7+ hours', f"{sleep['nights_7plus']} ({sleep['nights_7plus_pct']}%)")

        if sleep['status'] == 'concern':
            pdf.ln(2)
            pdf.set_font('Helvetica', 'I', 8)
            pdf.multi_cell(0, 4,
                'Note: Research shows <7 hours sleep increases injury risk by 1.7x. '
                'Aim for 7-8 hours consistently.')
        pdf.ln(4)

    # Stress
    if stress.get('available'):
        pdf.subsection('Stress Level')
        pdf.set_font('Helvetica', '', 9)

        pdf.key_value('Average stress', f"{stress['avg']}")
        pdf.key_value('Range', f"{stress['min']} - {stress['max']}")
        pdf.key_value('High stress days (>45)', f"{stress['high_stress_days']} ({stress['high_stress_pct']}%)")

        if stress.get('low_stress_recharge') and stress.get('high_stress_recharge'):
            pdf.key_value('Low stress recharge', f"+{stress['low_stress_recharge']} BB points")
            pdf.key_value('High stress recharge', f"+{stress['high_stress_recharge']} BB points")
        pdf.ln(4)

    # ============ PATTERNS PAGE ============
    pdf.add_page()
    pdf.section_header('PART 2: PATTERNS & CORRELATIONS')

    # Sedentary analysis
    if sed.get('available'):
        pdf.subsection('Sedentary Time Analysis')
        pdf.set_font('Helvetica', '', 9)

        pdf.key_value('Average sedentary hours', f"{sed['avg_hours']} hours/day")
        pdf.key_value('Days with 17+ hours sedentary', f"{sed['high_sed_days']} ({sed['high_sed_pct']}%)")

        if sed.get('correlation_found'):
            pdf.ln(2)
            pdf.set_font('Helvetica', 'B', 9)
            pdf.cell(0, 5, 'Sedentary Time vs Sleep Duration:', ln=True)

            # Table
            pdf.set_font('Helvetica', 'B', 8)
            pdf.set_fill_color(220, 220, 220)
            pdf.cell(60, 5, 'Sedentary Hours', 1, 0, 'C', True)
            pdf.cell(60, 5, 'Average Sleep', 1, 0, 'C', True)
            pdf.cell(60, 5, 'Impact', 1, 1, 'C', True)

            pdf.set_font('Helvetica', '', 8)
            if sed.get('low_sed_avg_sleep'):
                pdf.set_fill_color(200, 255, 200)
                pdf.cell(60, 5, '< 14 hours', 1, 0, 'C', True)
                pdf.cell(60, 5, f"{sed['low_sed_avg_sleep']} hours", 1, 0, 'C', True)
                pdf.cell(60, 5, 'Best sleep', 1, 1, 'C', True)

            if sed.get('med_sed_avg_sleep'):
                pdf.set_fill_color(255, 255, 200)
                pdf.cell(60, 5, '14-17 hours', 1, 0, 'C', True)
                pdf.cell(60, 5, f"{sed['med_sed_avg_sleep']} hours", 1, 0, 'C', True)
                pdf.cell(60, 5, 'Moderate', 1, 1, 'C', True)

            if sed.get('high_sed_avg_sleep'):
                pdf.set_fill_color(255, 200, 200)
                pdf.cell(60, 5, '17+ hours', 1, 0, 'C', True)
                pdf.cell(60, 5, f"{sed['high_sed_avg_sleep']} hours", 1, 0, 'C', True)
                pdf.cell(60, 5, 'Poor sleep', 1, 1, 'C', True)

            pdf.ln(2)
            pdf.set_font('Helvetica', 'I', 8)
            pdf.multi_cell(0, 4,
                'Key insight: Sedentary time appears to strongly predict sleep duration, '
                'regardless of exercise. Breaking up sitting throughout the day may improve sleep quality.')
        pdf.ln(4)

    # Day of week patterns
    dow = results.get('day_of_week', {})
    if dow.get('available'):
        pdf.subsection('Day of Week Patterns')
        pdf.set_font('Helvetica', '', 9)

        if dow.get('best_sleep_day') and dow.get('worst_sleep_day'):
            pdf.cell(0, 5, f"Best sleep day: {dow['best_sleep_day']} ({dow['by_day'][dow['best_sleep_day']]['avg_sleep']}h avg)", ln=True)
            pdf.cell(0, 5, f"Worst sleep day: {dow['worst_sleep_day']} ({dow['by_day'][dow['worst_sleep_day']]['avg_sleep']}h avg)", ln=True)

        if dow.get('best_bb_day') and dow.get('worst_bb_day'):
            pdf.cell(0, 5, f"Best Body Battery day: {dow['best_bb_day']} ({dow['by_day'][dow['best_bb_day']]['avg_bb']} avg)", ln=True)
            pdf.cell(0, 5, f"Worst Body Battery day: {dow['worst_bb_day']} ({dow['by_day'][dow['worst_bb_day']]['avg_bb']} avg)", ln=True)

        pdf.ln(2)

        # Day of week table
        pdf.set_font('Helvetica', 'B', 7)
        pdf.set_fill_color(220, 220, 220)
        cols = [26, 26, 26, 26, 30, 26, 30]
        for i, day in enumerate(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']):
            pdf.cell(cols[i], 5, day, 1, 0, 'C', True)
        pdf.ln()

        # Sleep row
        pdf.set_font('Helvetica', '', 7)
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for i, day in enumerate(day_order):
            val = dow['by_day'][day].get('avg_sleep')
            text = f"{val}h" if val else "-"
            pdf.cell(cols[i], 5, text, 1, 0, 'C')
        pdf.ln()

        # BB row
        for i, day in enumerate(day_order):
            val = dow['by_day'][day].get('avg_bb')
            text = str(int(val)) if val else "-"
            pdf.cell(cols[i], 5, text, 1, 0, 'C')
        pdf.ln()

        pdf.set_font('Helvetica', 'I', 7)
        pdf.cell(0, 4, 'Row 1: Avg Sleep | Row 2: Avg Body Battery', ln=True)
        pdf.ln(4)

    # Steps analysis
    steps = results.get('steps', {})
    if steps.get('available'):
        pdf.subsection('Activity Patterns')
        pdf.set_font('Helvetica', '', 9)

        pdf.key_value('Average daily steps', f"{steps['avg']:,.0f}")
        pdf.key_value('Range', f"{steps['min']:,} - {steps['max']:,}")
        pdf.key_value('Low activity days (<5k)', f"{steps['low_days']} ({steps['low_days_pct']}%)")
        pdf.key_value('Very active days (20k+)', f"{steps['very_active_days']}")
        pdf.key_value('Variability', steps['variability'].title())

        if steps['variability'] == 'high':
            pdf.ln(2)
            pdf.set_font('Helvetica', 'I', 8)
            pdf.multi_cell(0, 4,
                'Note: High variability (feast or famine pattern) may be harder on recovery than '
                'consistent moderate activity. Consider adding light movement on rest days.')

    # ============ RECOMMENDATIONS PAGE ============
    pdf.add_page()
    pdf.section_header('PART 3: RECOMMENDATIONS', color=(34, 139, 34))

    recommendations = results.get('recommendations', [])

    if recommendations:
        # Group by priority
        high_priority = [r for r in recommendations if r['priority'] == 'high']
        med_priority = [r for r in recommendations if r['priority'] == 'medium']
        low_priority = [r for r in recommendations if r['priority'] == 'low']

        if high_priority:
            pdf.subsection('High Priority')
            for rec in high_priority:
                pdf.set_font('Helvetica', 'B', 9)
                pdf.cell(0, 5, f"[{rec['category']}] {rec['finding']}", ln=True)
                pdf.set_font('Helvetica', '', 9)
                pdf.multi_cell(0, 4, f"Recommendation: {rec['recommendation']}")
                pdf.set_font('Helvetica', 'I', 8)
                pdf.multi_cell(0, 4, f"Science: {rec['science']}")
                pdf.ln(3)

        if med_priority:
            pdf.subsection('Medium Priority')
            for rec in med_priority:
                pdf.set_font('Helvetica', 'B', 9)
                pdf.cell(0, 5, f"[{rec['category']}] {rec['finding']}", ln=True)
                pdf.set_font('Helvetica', '', 9)
                pdf.multi_cell(0, 4, f"Recommendation: {rec['recommendation']}")
                pdf.ln(2)

        if low_priority:
            pdf.subsection('Lower Priority')
            for rec in low_priority:
                pdf.set_font('Helvetica', 'B', 9)
                pdf.cell(0, 5, f"[{rec['category']}] {rec['finding']}", ln=True)
                pdf.set_font('Helvetica', '', 9)
                pdf.multi_cell(0, 4, f"Recommendation: {rec['recommendation']}")
                pdf.ln(2)
    else:
        pdf.set_font('Helvetica', '', 10)
        pdf.multi_cell(0, 5,
            'Your metrics look relatively stable. Continue monitoring and consider the general '
            'health guidelines in the Science section below.')

    # ============ MONTHLY TRENDS PAGE ============
    pdf.add_page()
    pdf.section_header('APPENDIX A: MONTHLY TRENDS')

    monthly = results.get('monthly_trends', {})
    if monthly.get('available') and monthly.get('by_month'):
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(0, 5, f"Data spans {monthly['months_analyzed']} months:", ln=True)
        pdf.ln(2)

        # Monthly table
        pdf.set_font('Helvetica', 'B', 7)
        pdf.set_fill_color(220, 220, 220)
        cols = [25, 22, 22, 25, 25, 35, 36]
        headers = ['Month', 'RHR', 'BB', 'Sleep', 'Stress', 'Steps', 'Vig Min']
        for i, h in enumerate(headers):
            pdf.cell(cols[i], 5, h, 1, 0, 'C', True)
        pdf.ln()

        pdf.set_font('Helvetica', '', 7)
        for month, data in monthly['by_month'].items():
            # Format month name
            try:
                month_display = datetime.strptime(month, '%Y-%m').strftime('%b %Y')
            except:
                month_display = month

            pdf.cell(cols[0], 5, month_display, 1, 0, 'C')
            pdf.cell(cols[1], 5, str(data['avg_rhr'] or '-'), 1, 0, 'C')
            pdf.cell(cols[2], 5, str(int(data['avg_bb']) if data['avg_bb'] else '-'), 1, 0, 'C')
            pdf.cell(cols[3], 5, f"{data['avg_sleep']}h" if data['avg_sleep'] else '-', 1, 0, 'C')
            pdf.cell(cols[4], 5, str(int(data['avg_stress']) if data['avg_stress'] else '-'), 1, 0, 'C')
            pdf.cell(cols[5], 5, f"{data['avg_steps']:,.0f}" if data['avg_steps'] else '-', 1, 0, 'C')
            pdf.cell(cols[6], 5, str(int(data['total_vigorous']) if data['total_vigorous'] else '-'), 1, 0, 'C')
            pdf.ln()

    # ============ SCIENCE PAGE ============
    pdf.add_page()
    pdf.section_header('APPENDIX B: THE SCIENCE')

    science_sections = [
        ('Heart Rate & Recovery',
         ['A rise of 3-5 bpm in resting HR often indicates accumulated fatigue',
          'RHR typically drops during rest/taper periods as fitness is absorbed',
          'Morning RHR is most reliable when measured immediately upon waking',
          'Illness, alcohol, and poor sleep can artificially elevate RHR']),

        ('Sleep & Performance',
         ['Research shows <7 hours sleep increases injury risk by 1.7x (Milewski et al.)',
          'Sleep extension improves athletic performance metrics (Mah et al.)',
          'Growth hormone release peaks during deep sleep stages',
          'Consistent sleep schedule more important than occasional catch-up sleep']),

        ('Sedentary Behavior',
         ['"Active couch potato" syndrome: exercise doesn\'t fully offset prolonged sitting',
          'Breaking up sitting every 30-60 minutes improves metabolic markers',
          'Post-meal walks improve glucose response by 30-50%',
          'Light activity throughout day better than single exercise bout']),

        ('Stress & Recovery',
         ['High stress can throttle overnight recovery regardless of sleep duration',
          'Chronic stress elevates cortisol, impairing adaptation',
          'Stress management techniques: breathing exercises, meditation, nature exposure',
          'Recovery is when adaptation happens - training is just the stimulus']),
    ]

    for title, points in science_sections:
        pdf.subsection(title)
        pdf.set_font('Helvetica', '', 8)
        for point in points:
            pdf.cell(0, 4, '- ' + point, ln=True)
        pdf.ln(3)

    # ============ FINAL PAGE ============
    pdf.add_page()
    pdf.section_header('SUMMARY', color=(34, 139, 34))

    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(70, 130, 180)
    pdf.cell(0, 10, 'Key Takeaways', ln=True, align='C')
    pdf.set_text_color(0, 0, 0)

    pdf.set_font('Helvetica', '', 10)
    pdf.ln(3)

    # Dynamic summary based on findings
    takeaways = []

    if rhr.get('available'):
        if rhr['status'] == 'concern':
            takeaways.append(f"Your resting HR has risen {rhr['change']:+.1f} bpm - consider a recovery period.")
        else:
            takeaways.append(f"Your resting HR is stable at {rhr['current']} bpm.")

    if bb.get('available'):
        if bb['status'] == 'concern':
            takeaways.append(f"Body Battery wake values ({bb['current_wake']}) suggest recovery deficit.")
        elif bb['status'] == 'good':
            takeaways.append(f"Body Battery wake values ({bb['current_wake']}) indicate good recovery.")

    if sed.get('correlation_found'):
        takeaways.append("Reducing sedentary time appears to be a key lever for improving sleep.")

    if stress.get('available') and stress.get('low_stress_recharge') and stress.get('high_stress_recharge'):
        diff = stress['low_stress_recharge'] - stress['high_stress_recharge']
        if diff > 20:
            takeaways.append("Stress management significantly impacts your overnight recovery.")

    if not takeaways:
        takeaways.append("Continue monitoring your metrics and maintaining healthy habits.")

    for i, takeaway in enumerate(takeaways, 1):
        pdf.cell(0, 6, f"{i}. {takeaway}", ln=True)

    pdf.ln(10)

    pdf.set_font('Helvetica', 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 5,
        'This report was generated from your Garmin Connect data using the open-source '
        'Garmin Health Analyzer tool. The insights are based on patterns in your personal data '
        'and general health research. Always consult healthcare professionals for medical advice.',
        align='C')

    # Save PDF
    if output_path is None:
        output_path = 'Health_Insights_Report.pdf'

    pdf.output(output_path)
    print(f"PDF saved to: {output_path}")

    return output_path


def main():
    """Generate PDF report from data in the default directory."""
    try:
        generate_insights_pdf()
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
