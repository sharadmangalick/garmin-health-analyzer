#!/usr/bin/env python3
"""CLI interface for Garmin Data Analyzer."""

import json
from datetime import date, timedelta

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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


if __name__ == "__main__":
    cli()
