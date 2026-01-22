#!/usr/bin/env python3
"""CLI interface for Garmin Data Analyzer."""

import json
from datetime import date, timedelta

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

from config import config
from garmin_client import GarminClient
from data_analyzer import GarminDataAnalyzer
from pdf_generator import generate_insights_pdf
from html_generator import generate_insights_html

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Garmin Data Analyzer - Analyze your Garmin Connect data with Claude AI."""
    pass


@cli.command()
@click.option("--days", "-d", default=7, help="Number of days to fetch (default: 7)")
@click.option("--force", "-f", is_flag=True, help="Force re-fetch even if cached")
@click.option("--activities", "-a", is_flag=True, help="Fetch only activities")
@click.option("--sleep", "-s", is_flag=True, help="Fetch only sleep data")
@click.option("--heart-rate", "-h", "heart_rate", is_flag=True, help="Fetch only heart rate data")
@click.option("--summaries", "-u", is_flag=True, help="Fetch only daily summaries")
@click.option("--vo2max", "-v", is_flag=True, help="Fetch only VO2 max data")
def fetch(days: int, force: bool, activities: bool, sleep: bool, heart_rate: bool, summaries: bool, vo2max: bool):
    """Fetch data from Garmin Connect.

    Examples:
        python main.py fetch --days 7
        python main.py fetch -d 30 --force
        python main.py fetch --activities --sleep
        python main.py fetch --vo2max
    """
    config.ensure_directories()

    client = GarminClient()
    if not client.login():
        raise click.Abort()

    # If no specific type selected, fetch all
    fetch_all = not any([activities, sleep, heart_rate, summaries, vo2max])

    console.print(Panel(f"Fetching data for the last {days} days", title="Garmin Fetch"))

    if fetch_all or activities:
        client.fetch_activities(days, force)
    if fetch_all or sleep:
        client.fetch_sleep(days, force)
    if fetch_all or heart_rate:
        client.fetch_heart_rate(days, force)
    if fetch_all or summaries:
        client.fetch_daily_summaries(days, force)
    if fetch_all or vo2max:
        client.fetch_vo2max(days, force)

    console.print("\n[green]Fetch complete![/green]")


@cli.command()
@click.option("--days", "-d", default=7, help="Number of days to show (default: 7)")
def show(days: int):
    """Show a summary of your fetched data.

    Examples:
        python main.py show
        python main.py show -d 14
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    console.print(Panel(f"Data Summary for {start_date} to {end_date}", title="Garmin Data"))

    # Show activities
    if config.activities_dir.exists():
        activities = []
        for filepath in config.activities_dir.glob("*.json"):
            with open(filepath) as f:
                activity = json.load(f)
                activity_date = activity.get("startTimeLocal", "")[:10]
                if activity_date >= start_date.isoformat():
                    activities.append(activity)

        if activities:
            table = Table(title="Activities")
            table.add_column("Date", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Duration", style="yellow")
            table.add_column("Distance", style="blue")
            table.add_column("Avg HR", style="red")

            for a in sorted(activities, key=lambda x: x.get("startTimeLocal", ""), reverse=True):
                activity_date = a.get("startTimeLocal", "")[:10]
                activity_type = a.get("activityType", {}).get("typeKey", "Unknown")
                duration_mins = a.get("duration", 0) / 60
                distance_km = a.get("distance", 0) / 1000
                avg_hr = a.get("averageHR", "N/A")

                table.add_row(
                    activity_date,
                    activity_type,
                    f"{duration_mins:.0f} min",
                    f"{distance_km:.2f} km" if distance_km > 0 else "-",
                    str(avg_hr)
                )

            console.print(table)
        else:
            console.print("[yellow]No activities found for this period[/yellow]")
    else:
        console.print("[yellow]No activity data - run 'fetch' first[/yellow]")

    # Show sleep summary
    if config.sleep_dir.exists():
        sleep_data = []
        for i in range(days):
            current_date = end_date - timedelta(days=i)
            filepath = config.sleep_dir / f"{current_date.isoformat()}.json"
            if filepath.exists():
                with open(filepath) as f:
                    sleep_data.append(json.load(f))

        if sleep_data:
            table = Table(title="Sleep")
            table.add_column("Date", style="cyan")
            table.add_column("Total", style="green")
            table.add_column("Deep", style="blue")
            table.add_column("REM", style="magenta")

            for s in sleep_data:
                daily = s.get("dailySleepDTO", {})
                sleep_date = daily.get("calendarDate", "Unknown")
                total_hrs = daily.get("sleepTimeSeconds", 0) / 3600
                deep_hrs = daily.get("deepSleepSeconds", 0) / 3600
                rem_hrs = daily.get("remSleepSeconds", 0) / 3600

                if total_hrs > 0:
                    table.add_row(
                        sleep_date,
                        f"{total_hrs:.1f} hrs",
                        f"{deep_hrs:.1f} hrs",
                        f"{rem_hrs:.1f} hrs"
                    )

            console.print(table)
    else:
        console.print("[yellow]No sleep data - run 'fetch' first[/yellow]")


@cli.command()
def status():
    """Show configuration status and data summary."""
    console.print(Panel("Configuration & Data Status", title="Status"))

    # Check Garmin session
    if config.has_garmin_session():
        console.print("[green]Garmin session saved (will auto-login)[/green]")
    else:
        console.print("[yellow]No Garmin session - will prompt for login on fetch[/yellow]")

    # Check data directories
    console.print("\n[bold]Cached Data:[/bold]")

    if config.activities_dir.exists():
        count = len(list(config.activities_dir.glob("*.json")))
        console.print(f"  Activities: {count} files")
    else:
        console.print("  Activities: No data")

    if config.sleep_dir.exists():
        count = len(list(config.sleep_dir.glob("*.json")))
        console.print(f"  Sleep: {count} files")
    else:
        console.print("  Sleep: No data")

    if config.heart_rate_dir.exists():
        count = len(list(config.heart_rate_dir.glob("*.json")))
        console.print(f"  Heart Rate: {count} files")
    else:
        console.print("  Heart Rate: No data")

    if config.daily_summaries_dir.exists():
        count = len(list(config.daily_summaries_dir.glob("*.json")))
        console.print(f"  Daily Summaries: {count} files")
    else:
        console.print("  Daily Summaries: No data")

    if config.vo2max_dir.exists():
        count = len(list(config.vo2max_dir.glob("*.json")))
        console.print(f"  VO2 Max: {count} files")
    else:
        console.print("  VO2 Max: No data")


@cli.command()
def clear():
    """Clear all cached data."""
    import shutil

    if click.confirm("This will delete all cached Garmin data. Continue?"):
        for data_dir in [config.activities_dir, config.sleep_dir, config.heart_rate_dir, config.daily_summaries_dir, config.vo2max_dir]:
            if data_dir.exists():
                shutil.rmtree(data_dir)
        config.ensure_directories()
        console.print("[green]Cached data cleared.[/green]")


@cli.command()
def logout():
    """Clear saved Garmin session (will require re-login on next fetch)."""
    if config.session_file.exists():
        config.session_file.unlink()
        console.print("[green]Garmin session cleared. You will need to log in again on next fetch.[/green]")
    else:
        console.print("[yellow]No saved session to clear.[/yellow]")


@cli.command()
@click.option("--output", "-o", default=None, help="Output filename (auto-detects format from extension)")
@click.option("--pdf/--no-pdf", default=True, help="Generate PDF report (default: yes)")
@click.option("--html", is_flag=True, help="Generate HTML report instead of PDF")
@click.option("--text", "-t", is_flag=True, help="Print text summary to console")
def analyze(output: str, pdf: bool, html: bool, text: bool):
    """Analyze your Garmin data and generate insights report.

    This command analyzes your fetched Garmin data to identify:
    - Recovery status (resting HR, Body Battery trends)
    - VO2 max trends and fitness level
    - Sleep patterns and correlations
    - Sedentary time impact on health metrics
    - Stress and recovery relationships
    - Day-of-week patterns
    - Monthly trends

    Examples:
        python main.py analyze
        python main.py analyze --output my_report.pdf
        python main.py analyze --html --output report.html
        python main.py analyze --text --no-pdf
    """
    # Check if data exists
    if not config.daily_summaries_dir.exists() or not any(config.daily_summaries_dir.glob("*.json")):
        console.print("[red]No data found. Please run 'python main.py fetch' first.[/red]")
        raise click.Abort()

    console.print(Panel("Analyzing your Garmin data...", title="Analysis"))

    try:
        # Run analysis
        analyzer = GarminDataAnalyzer(str(config.data_dir))
        load_result = analyzer.load_data()

        console.print(f"  Loaded {load_result['daily_summaries']} days of daily summaries")
        console.print(f"  Loaded {load_result['sleep']} sleep records")
        console.print(f"  Loaded {load_result['heart_rate']} heart rate records")
        console.print(f"  Loaded {load_result['vo2max']} VO2 max records")

        if load_result['date_range']:
            console.print(f"  Date range: {load_result['date_range'][0]} to {load_result['date_range'][1]}")

        # Run analysis
        results = analyzer.analyze_all()

        # Show text summary if requested or no output
        if text or (not pdf and not html):
            console.print("\n")
            console.print(analyzer.get_summary_text())

        # Generate HTML report
        if html:
            console.print("\n[bold]Generating HTML report...[/bold]")
            output_path = output or "Health_Insights_Report.html"
            generate_insights_html(output_path, str(config.data_dir))
            console.print(f"\n[green]Report saved to: {output_path}[/green]")
        # Generate PDF report
        elif pdf:
            console.print("\n[bold]Generating PDF report...[/bold]")
            output_path = output or "Health_Insights_Report.pdf"
            generate_insights_pdf(output_path, str(config.data_dir))
            console.print(f"\n[green]Report saved to: {output_path}[/green]")

    except Exception as e:
        console.print(f"[red]Error during analysis: {e}[/red]")
        raise click.Abort()


@cli.command()
def quickstart():
    """Interactive guide to get started with Garmin Health Analyzer.

    This walks you through:
    1. Logging into Garmin Connect
    2. Fetching your data
    3. Running analysis
    4. Understanding your results
    """
    console.print(Panel.fit(
        "[bold cyan]Welcome to Garmin Health Analyzer![/bold cyan]\n\n"
        "This tool helps you understand your health data from Garmin Connect.\n"
        "Let's get you set up!",
        title="Quickstart Guide"
    ))

    # Step 1: Check existing data
    console.print("\n[bold]Step 1: Check existing data[/bold]")

    has_data = False
    if config.daily_summaries_dir.exists():
        count = len(list(config.daily_summaries_dir.glob("*.json")))
        if count > 0:
            has_data = True
            console.print(f"  [green]Found {count} days of data already cached![/green]")

    if not has_data:
        console.print("  [yellow]No data found yet.[/yellow]")

    # Step 2: Fetch data
    console.print("\n[bold]Step 2: Fetch data from Garmin[/bold]")

    if has_data:
        if click.confirm("  Would you like to fetch more data?", default=False):
            days = click.prompt("  How many days to fetch?", default=30, type=int)
            console.print(f"\n  Run: [cyan]python main.py fetch --days {days}[/cyan]")
            if click.confirm("  Run this command now?", default=True):
                from click.testing import CliRunner
                runner = CliRunner()
                result = runner.invoke(fetch, ["--days", str(days)])
                console.print(result.output)
    else:
        console.print("  You need to fetch data from Garmin Connect first.")
        console.print("  This requires your Garmin account credentials.")
        days = click.prompt("  How many days of history to fetch?", default=90, type=int)
        console.print(f"\n  Run: [cyan]python main.py fetch --days {days}[/cyan]")
        console.print("  [yellow]Note: Run this command in your terminal to enter credentials.[/yellow]")

    # Step 3: Analyze
    console.print("\n[bold]Step 3: Analyze your data[/bold]")

    if has_data:
        console.print("  Ready to analyze! This will:")
        console.print("  - Calculate recovery trends (RHR, Body Battery)")
        console.print("  - Find sleep patterns and correlations")
        console.print("  - Identify lifestyle factors affecting health")
        console.print("  - Generate personalized recommendations")

        if click.confirm("\n  Would you like to run the analysis now?", default=True):
            from click.testing import CliRunner
            runner = CliRunner()
            result = runner.invoke(analyze, ["--text"])
            console.print(result.output)

            if click.confirm("\n  Generate a PDF report?", default=True):
                result = runner.invoke(analyze, [])
                console.print(result.output)
    else:
        console.print("  After fetching data, run: [cyan]python main.py analyze[/cyan]")

    console.print("\n[bold]Available Commands:[/bold]")
    console.print("  [cyan]python main.py fetch --days N[/cyan]  - Fetch N days of data")
    console.print("  [cyan]python main.py analyze[/cyan]         - Run analysis and generate PDF")
    console.print("  [cyan]python main.py analyze --text[/cyan]  - Show text summary")
    console.print("  [cyan]python main.py show[/cyan]            - Show recent data")
    console.print("  [cyan]python main.py status[/cyan]          - Check data status")

    console.print("\n[green]Happy analyzing![/green]")


# ==================== EMAIL COMMAND GROUP ====================

@cli.group()
def email():
    """Weekly training email system commands.

    Generate and send personalized weekly training plans based on your
    Garmin health data and AI-powered coaching recommendations.

    Examples:
        python main.py email setup      # Configure your profile
        python main.py email preview    # Preview the weekly plan
        python main.py email send       # Generate and send report
        python main.py email schedule   # Show scheduling info
    """
    pass


@email.command()
def setup():
    """Interactive setup wizard for email configuration.

    Configure your:
    - Email address
    - Race goal and date
    - Training preferences
    """
    from user_config import UserConfig

    console.print(Panel.fit(
        "[bold cyan]Weekly Training Email Setup[/bold cyan]\n\n"
        "This wizard will configure your training email system.\n"
        "Your settings will be saved for future use.",
        title="Setup Wizard"
    ))

    user_config = UserConfig()
    current = user_config.to_dict()

    console.print("\n[bold]Current Configuration:[/bold]")
    console.print(f"  Email: {current['email']}")
    console.print(f"  Name: {current['name']}")
    console.print(f"  Goal: {current['goal_target']} {current['goal_type']}")
    console.print(f"  Race Date: {current['goal_date']}")
    console.print(f"  Weekly Mileage: {current['current_weekly_mileage']} miles")

    if not Confirm.ask("\nWould you like to update these settings?", default=True):
        console.print("[yellow]Setup cancelled.[/yellow]")
        return

    # Collect new settings
    console.print("\n[bold]Enter your settings (press Enter to keep current value):[/bold]\n")

    email_addr = Prompt.ask(
        "Email address",
        default=current['email'] if current['email'] != "your@gmail.com" else ""
    )
    if email_addr:
        user_config.update(email=email_addr)

    name = Prompt.ask("Your name", default=current['name'])
    if name:
        user_config.update(name=name)

    console.print("\n[bold]Race Goal:[/bold]")
    goal_type = Prompt.ask(
        "Race type",
        choices=["marathon", "half_marathon", "10k", "5k"],
        default=current['goal_type']
    )
    user_config.update(goal_type=goal_type)

    goal_target = Prompt.ask(
        "Goal target (e.g., 'sub-4-hour', 'sub-2-hour', 'finish')",
        default=current['goal_target']
    )
    user_config.update(goal_target=goal_target)

    # Calculate goal time in minutes
    goal_time_input = Prompt.ask(
        "Goal time in minutes (e.g., 240 for 4 hours)",
        default=str(current['goal_time_minutes'])
    )
    try:
        goal_time = int(goal_time_input)
        user_config.update(goal_time_minutes=goal_time)
    except ValueError:
        console.print("[yellow]Invalid time, keeping current value[/yellow]")

    goal_date = Prompt.ask(
        "Race date (YYYY-MM-DD)",
        default=current['goal_date']
    )
    user_config.update(goal_date=goal_date)

    console.print("\n[bold]Training Preferences:[/bold]")
    weekly_mileage = Prompt.ask(
        "Current weekly mileage",
        default=str(current['current_weekly_mileage'])
    )
    try:
        user_config.update(current_weekly_mileage=int(weekly_mileage))
    except ValueError:
        pass

    experience = Prompt.ask(
        "Experience level",
        choices=["beginner", "intermediate", "advanced"],
        default=current['experience_level']
    )
    user_config.update(experience_level=experience)

    long_run_day = Prompt.ask(
        "Preferred long run day",
        choices=["saturday", "sunday"],
        default=current['preferred_long_run_day']
    )
    user_config.update(preferred_long_run_day=long_run_day)

    # Save and show summary
    user_config.save()

    console.print("\n[green]Configuration saved![/green]\n")

    # Show summary
    updated = user_config.to_dict()
    table = Table(title="Your Training Profile")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Email", updated['email'])
    table.add_row("Name", updated['name'])
    table.add_row("Goal", f"{updated['goal_target']} {updated['goal_type']}")
    table.add_row("Race Date", updated['goal_date'])
    table.add_row("Weeks to Race", str(updated['weeks_until_race']))
    table.add_row("Training Phase", updated['training_phase'].title())
    table.add_row("Target Pace", f"{updated['target_pace']}/mile")
    table.add_row("Weekly Mileage", f"{updated['current_weekly_mileage']} miles")

    console.print(table)

    console.print("\n[bold]Next Steps:[/bold]")
    console.print("  1. Ensure ANTHROPIC_API_KEY is set in your .env file")
    console.print("  2. Run [cyan]python main.py email preview[/cyan] to test")
    console.print("  3. Run [cyan]python main.py email send[/cyan] to generate and send")


@email.command()
@click.option("--days", "-d", default=14, help="Days of data to analyze (default: 14)")
@click.option("--no-fetch", is_flag=True, help="Use cached data, don't fetch new data")
def preview(days: int, no_fetch: bool):
    """Preview the weekly training plan without sending.

    Generates a training plan based on your Garmin data and displays
    it in the console. Useful for testing before sending.

    For enterprise users (no API key): This prepares the analysis context.
    Use Claude Code to generate the training plan from the context file.

    Examples:
        python main.py email preview
        python main.py email preview --no-fetch
        python main.py email preview -d 30
    """
    from weekly_report import WeeklyReportGenerator

    console.print(Panel("Generating Training Plan Preview", title="Preview"))

    try:
        generator = WeeklyReportGenerator()

        # Check configuration
        if not generator.user_config.is_configured():
            console.print("[yellow]Warning: User not configured. Run 'python main.py email setup' first.[/yellow]")
            console.print("[yellow]Using default settings...[/yellow]\n")

        # Check if API key is available
        has_api_key = config.has_anthropic_key()

        if has_api_key:
            # Full workflow with API
            with console.status("[bold blue]Generating report..."):
                result = generator.generate_full_report(
                    fetch_data=not no_fetch,
                    days=days,
                    use_mcp=False
                )

            # Display preview
            console.print("\n" + "=" * 60)
            console.print(generator.get_preview_text())
            console.print("=" * 60 + "\n")

            # Show email subject
            console.print(f"[bold]Email Subject:[/bold] {result['email']['subject']}\n")

            # Save HTML preview
            html_path = config.data_dir / "preview_email.html"
            with open(html_path, 'w') as f:
                f.write(result['email']['html_body'])
            console.print(f"[green]HTML preview saved to: {html_path}[/green]")
            console.print("Open this file in a browser to see the full email.\n")
        else:
            # Enterprise workflow - prepare for Claude Code
            console.print("[yellow]No API key found - using Claude Code workflow[/yellow]\n")

            with console.status("[bold blue]Analyzing data..."):
                result = generator.prepare_analysis_only(
                    fetch_data=not no_fetch,
                    days=days,
                    use_mcp=False
                )

            console.print("[green]Analysis complete![/green]\n")

            # Show analysis summary
            console.print("[bold]Analysis Summary:[/bold]")
            analysis = result['analysis']
            if analysis.get('resting_hr', {}).get('available'):
                rhr = analysis['resting_hr']
                console.print(f"  Resting HR: {rhr.get('current')} bpm (trend: {rhr.get('trend')})")
            if analysis.get('body_battery', {}).get('available'):
                bb = analysis['body_battery']
                console.print(f"  Body Battery: {bb.get('current_wake')} wake avg (trend: {bb.get('trend')})")
            if analysis.get('sleep', {}).get('available'):
                sleep = analysis['sleep']
                console.print(f"  Sleep: {sleep.get('avg_hours')} hrs avg")

            console.print(f"\n[bold]Context saved to:[/bold] {result['context_file']}")
            console.print("\n[bold cyan]Next Steps (for Claude Code):[/bold cyan]")
            console.print("  1. Read the context file above")
            console.print("  2. Generate a training plan following the format in the context")
            console.print("  3. Save the plan to data/training_plan.json")
            console.print("  4. Run: python main.py email send --use-plan")

    except Exception as e:
        console.print(f"[red]Error generating preview: {e}[/red]")
        raise click.Abort()


@email.command()
@click.option("--days", "-d", default=14, help="Days of data to analyze (default: 14)")
@click.option("--no-fetch", is_flag=True, help="Use cached data, don't fetch new data")
@click.option("--use-plan", is_flag=True, help="Use existing training plan from data/training_plan.json")
@click.option("--plan-file", type=click.Path(exists=True), help="Path to training plan JSON file")
def send(days: int, no_fetch: bool, use_plan: bool, plan_file: str):
    """Generate and queue weekly training report for sending.

    This generates the full report and saves it for sending via Gmail MCP.

    For enterprise users (no API key):
      1. First run 'email preview' to generate analysis
      2. Have Claude Code generate the training plan
      3. Run 'email send --use-plan' to complete and send

    Examples:
        python main.py email send
        python main.py email send --no-fetch
        python main.py email send --use-plan
        python main.py email send --plan-file path/to/plan.json
    """
    import json as json_module
    from weekly_report import WeeklyReportGenerator

    console.print(Panel("Generating Weekly Training Report", title="Send Report"))

    try:
        generator = WeeklyReportGenerator()

        # Check configuration
        if not generator.user_config.is_configured():
            console.print("[red]Error: User not configured.[/red]")
            console.print("Run [cyan]python main.py email setup[/cyan] first.")
            raise click.Abort()

        training_plan = None

        # Load existing plan if specified
        if plan_file:
            with open(plan_file, 'r') as f:
                training_plan = json_module.load(f)
            console.print(f"[green]Loaded training plan from: {plan_file}[/green]\n")
        elif use_plan:
            default_plan_path = config.data_dir / "training_plan.json"
            if not default_plan_path.exists():
                console.print("[red]Error: No training plan found at data/training_plan.json[/red]")
                console.print("Generate a plan first or specify --plan-file")
                raise click.Abort()
            with open(default_plan_path, 'r') as f:
                training_plan = json_module.load(f)
            console.print(f"[green]Loaded training plan from: {default_plan_path}[/green]\n")

        # Check if we have a plan or can generate one
        has_api_key = config.has_anthropic_key()

        if training_plan is None and not has_api_key:
            console.print("[yellow]No API key found and no training plan provided.[/yellow]")
            console.print("\n[bold]Enterprise User Workflow:[/bold]")
            console.print("  1. Run [cyan]python main.py email preview[/cyan] to prepare analysis")
            console.print("  2. Have Claude Code generate the training plan from the context")
            console.print("  3. Save the plan to data/training_plan.json")
            console.print("  4. Run [cyan]python main.py email send --use-plan[/cyan]")
            raise click.Abort()

        # Generate report
        with console.status("[bold blue]Generating report..."):
            if training_plan:
                # First run analysis, then complete with provided plan
                generator.prepare_analysis_only(
                    fetch_data=not no_fetch,
                    days=days,
                    use_mcp=False
                )
                result = generator.complete_report(training_plan)
            else:
                # Full workflow with API key
                result = generator.generate_full_report(
                    fetch_data=not no_fetch,
                    days=days,
                    use_mcp=False
                )

        console.print("\n[green]Report generated successfully![/green]\n")

        # Show summary
        table = Table(title="Report Summary")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Recipient", generator.user_config.email)
        table.add_row("Subject", result['email']['subject'])
        table.add_row("Email File", result['email_file'])

        week_summary = result['training_plan'].get('week_summary', {})
        table.add_row("Total Miles", str(week_summary.get('total_miles', 'N/A')))
        table.add_row("Training Phase", week_summary.get('training_phase', 'N/A').title())

        console.print(table)

        console.print("\n[bold]To send the email:[/bold]")
        console.print("  If using Claude Code with Gmail MCP:")
        email_file = result['email_file']
        console.print(f"    Ask Claude to 'Send the email at {email_file}'")
        console.print("\n  Or manually send via your email client using the HTML content.")

    except click.Abort:
        raise
    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]")
        raise click.Abort()


@email.command()
@click.option("--days", "-d", default=14, help="Days of data to analyze (default: 14)")
@click.option("--no-fetch", is_flag=True, help="Use cached data, don't fetch new data")
def prepare(days: int, no_fetch: bool):
    """Prepare analysis and context for Claude Code to generate training plan.

    This is for enterprise users who don't have a standalone API key.
    The workflow is:
      1. Run this command to fetch data and create analysis context
      2. Claude Code reads the context and generates a training plan
      3. Run 'email send --use-plan' to create and queue the email

    Examples:
        python main.py email prepare
        python main.py email prepare --days 30
    """
    from weekly_report import WeeklyReportGenerator

    console.print(Panel("Preparing Analysis for Claude Code", title="Prepare"))

    try:
        generator = WeeklyReportGenerator()

        # Check configuration
        if not generator.user_config.is_configured():
            console.print("[yellow]Warning: User not configured. Run 'python main.py email setup' first.[/yellow]\n")

        with console.status("[bold blue]Fetching and analyzing data..."):
            result = generator.prepare_analysis_only(
                fetch_data=not no_fetch,
                days=days,
                use_mcp=False
            )

        console.print("[green]Analysis complete![/green]\n")

        # Show user config summary
        user = result['user_config']
        console.print("[bold]User Profile:[/bold]")
        console.print(f"  Name: {user['name']}")
        console.print(f"  Goal: {user['goal_target']} {user['goal_type']}")
        console.print(f"  Race Date: {user['goal_date']} ({user['weeks_until_race']} weeks away)")
        console.print(f"  Training Phase: {user['training_phase']}")
        console.print(f"  Target Pace: {user['target_pace']}/mile")

        # Show analysis summary
        console.print("\n[bold]Health Analysis:[/bold]")
        analysis = result['analysis']

        if analysis.get('resting_hr', {}).get('available'):
            rhr = analysis['resting_hr']
            status = "[green]Good[/green]" if rhr.get('status') == 'good' else "[yellow]Normal[/yellow]" if rhr.get('status') == 'normal' else "[red]Concern[/red]"
            console.print(f"  Resting HR: {rhr.get('current')} bpm ({rhr.get('trend')}) - {status}")

        if analysis.get('body_battery', {}).get('available'):
            bb = analysis['body_battery']
            status = "[green]Good[/green]" if bb.get('status') == 'good' else "[yellow]Normal[/yellow]" if bb.get('status') == 'normal' else "[red]Concern[/red]"
            console.print(f"  Body Battery: {bb.get('current_wake')} wake avg ({bb.get('trend')}) - {status}")

        if analysis.get('sleep', {}).get('available'):
            sleep = analysis['sleep']
            status = "[green]Good[/green]" if sleep.get('status') == 'good' else "[yellow]Normal[/yellow]" if sleep.get('status') == 'normal' else "[red]Concern[/red]"
            console.print(f"  Sleep: {sleep.get('avg_hours')} hrs avg - {status}")

        if analysis.get('stress', {}).get('available'):
            stress = analysis['stress']
            console.print(f"  Stress: {stress.get('avg')} avg ({stress.get('high_stress_pct')}% high stress days)")

        console.print(f"\n[bold]Context file:[/bold] {result['context_file']}")
        console.print(f"[bold]Training plan output:[/bold] {config.data_dir / 'training_plan.json'}")

        console.print("\n" + "=" * 60)
        console.print("[bold cyan]NEXT STEP FOR CLAUDE CODE:[/bold cyan]")
        console.print("=" * 60)
        console.print(f"""
Read the context file at: {result['context_file']}

Generate a 7-day training plan as JSON with this structure:
{{
  "week_summary": {{"total_miles": <num>, "training_phase": "<phase>", "focus": "<text>"}},
  "daily_plan": [
    {{"day": "Monday", "workout_type": "<type>", "title": "<title>",
     "distance_miles": <num>, "description": "<text>", "notes": "<text>"}}
    ... (all 7 days)
  ],
  "coaching_notes": ["<note1>", "<note2>", "<note3>"],
  "recovery_recommendations": ["<rec1>"] (if needed based on health data)
}}

Save the plan to: {config.data_dir / 'training_plan.json'}

Then run: python main.py email send --use-plan
""")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@email.command()
def schedule():
    """Show scheduling information for automated weekly reports.

    Displays instructions for setting up automated weekly emails
    using macOS launchd.
    """
    from user_config import user_config

    console.print(Panel("Scheduling Weekly Reports", title="Schedule"))

    current = user_config.to_dict()

    console.print(f"[bold]Current Schedule Settings:[/bold]")
    console.print(f"  Email Day: {current['email_day'].title()}")
    console.print(f"  Email Time: {current['email_time']}")
    console.print(f"  Timezone: {current['timezone']}")

    console.print("\n[bold]To set up automated weekly emails:[/bold]")
    console.print("\n1. Copy the launchd plist to your LaunchAgents folder:")
    console.print("   [cyan]cp launchd/com.garmin.weekly-report.plist ~/Library/LaunchAgents/[/cyan]")

    console.print("\n2. Edit the plist to set the correct paths and schedule:")
    console.print("   [cyan]nano ~/Library/LaunchAgents/com.garmin.weekly-report.plist[/cyan]")

    console.print("\n3. Load the schedule:")
    console.print("   [cyan]launchctl load ~/Library/LaunchAgents/com.garmin.weekly-report.plist[/cyan]")

    console.print("\n4. Verify it's loaded:")
    console.print("   [cyan]launchctl list | grep garmin[/cyan]")

    console.print("\n[bold]To unload/stop:[/bold]")
    console.print("   [cyan]launchctl unload ~/Library/LaunchAgents/com.garmin.weekly-report.plist[/cyan]")

    console.print("\n[bold]Note:[/bold] For Gmail MCP integration, you'll need to run this through")
    console.print("Claude Code or set up a script that handles the email sending.")


@email.command()
def status():
    """Show current email system status and configuration."""
    from user_config import user_config

    console.print(Panel("Email System Status", title="Status"))

    # Check user config
    console.print("[bold]User Configuration:[/bold]")
    if user_config.is_configured():
        console.print(f"  [green]Configured[/green] - Email: {user_config.email}")
        console.print(f"  Name: {user_config.name}")
        console.print(f"  Goal: {user_config.goal_target} {user_config.goal_type}")
        console.print(f"  Race Date: {user_config.goal_date}")
        console.print(f"  Weeks to Race: {user_config.weeks_until_race()}")
    else:
        console.print("  [yellow]Not configured[/yellow] - Run 'python main.py email setup'")

    # Check API key
    console.print("\n[bold]API Configuration:[/bold]")
    if config.has_anthropic_key():
        console.print("  [green]ANTHROPIC_API_KEY: Set[/green] (direct API mode)")
    else:
        console.print("  [yellow]ANTHROPIC_API_KEY: Not set[/yellow] (Claude Code mode)")
        console.print("  [dim]Enterprise users: Use 'email prepare' + Claude Code workflow[/dim]")

    # Check Garmin session
    console.print("\n[bold]Garmin Connection:[/bold]")
    if config.has_garmin_session():
        console.print("  [green]Session saved[/green] - Will auto-login")
    else:
        console.print("  [yellow]No session[/yellow] - Will prompt for login")

    # Check data
    console.print("\n[bold]Data Status:[/bold]")
    if config.daily_summaries_dir.exists():
        count = len(list(config.daily_summaries_dir.glob("*.json")))
        if count > 0:
            console.print(f"  [green]{count} days of data available[/green]")
        else:
            console.print("  [yellow]No data[/yellow] - Run 'python main.py fetch'")
    else:
        console.print("  [yellow]No data[/yellow] - Run 'python main.py fetch'")

    # Check email queue
    console.print("\n[bold]Email Queue:[/bold]")
    if config.email_queue_dir.exists():
        pending = list(config.email_queue_dir.glob("*.json"))
        if pending:
            console.print(f"  [yellow]{len(pending)} emails pending[/yellow]")
            for p in pending[:3]:
                console.print(f"    - {p.name}")
        else:
            console.print("  [dim]No pending emails[/dim]")
    else:
        console.print("  [dim]No pending emails[/dim]")


if __name__ == "__main__":
    cli()
