"""Weekly Report Orchestrator - Ties together data fetching, analysis, AI coaching, and email delivery.

This module supports two modes of operation:
1. MCP Mode: Uses Garmin MCP for data fetching and Gmail MCP for email delivery
2. Direct Mode: Uses GarminClient for data and stores email for manual sending

When run from Claude Code with MCP servers configured, it will use the MCP tools.
When run standalone (e.g., from launchd), it uses direct API access.
"""

import json
import os
import sys
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

from config import config
from user_config import UserConfig, user_config
from data_analyzer import GarminDataAnalyzer
from ai_coach import AICoach
from email_generator import EmailGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WeeklyReportGenerator:
    """Orchestrates the weekly training report generation and delivery."""

    def __init__(
        self,
        user_config: Optional[UserConfig] = None,
        data_dir: Optional[str] = None
    ):
        self.user_config = user_config or UserConfig()
        self.data_dir = Path(data_dir) if data_dir else config.data_dir
        self.analyzer = GarminDataAnalyzer(str(self.data_dir))
        self.ai_coach = None  # Initialized lazily
        self.email_generator = EmailGenerator()

        # Store generated content for preview/debugging
        self.last_analysis = None
        self.last_training_plan = None
        self.last_email = None

    def _init_ai_coach(self, require_api: bool = False):
        """Initialize AI coach lazily."""
        if self.ai_coach is None:
            # Check if API key is available
            api_key = os.getenv("ANTHROPIC_API_KEY")
            self.ai_coach = AICoach(api_key=api_key, use_api=bool(api_key))

        if require_api and not self.ai_coach.use_api:
            raise RuntimeError(
                "No Anthropic API key available. For enterprise users, "
                "use prepare_for_claude_code() instead."
            )

    def fetch_garmin_data(self, days: int = 14, use_mcp: bool = False) -> bool:
        """
        Fetch recent Garmin data.

        Args:
            days: Number of days of data to fetch
            use_mcp: If True, indicates MCP should be used (called from Claude Code)

        Returns:
            True if data was successfully fetched/available
        """
        if use_mcp:
            # When use_mcp is True, the caller (Claude Code) should use the Garmin MCP
            # to fetch data before calling this method. We just verify data exists.
            logger.info("MCP mode: Expecting data to be fetched via Garmin MCP")
            return self._verify_data_exists()

        # Direct mode: use GarminClient
        try:
            from garmin_client import GarminClient
            client = GarminClient()

            if not client.login():
                logger.error("Failed to login to Garmin Connect")
                return False

            logger.info(f"Fetching {days} days of Garmin data...")
            client.fetch_all(days=days, force=False)
            logger.info("Garmin data fetch complete")
            return True

        except Exception as e:
            logger.error(f"Error fetching Garmin data: {e}")
            return False

    def _verify_data_exists(self) -> bool:
        """Check if sufficient data exists for analysis."""
        daily_summaries_dir = self.data_dir / "daily_summaries"
        if not daily_summaries_dir.exists():
            return False

        files = list(daily_summaries_dir.glob("*.json"))
        return len(files) >= 7  # Need at least a week of data

    def run_analysis(self) -> dict:
        """Run health data analysis."""
        logger.info("Loading and analyzing Garmin data...")

        load_result = self.analyzer.load_data()
        logger.info(f"Loaded {load_result['daily_summaries']} days of data")

        if load_result['daily_summaries'] == 0:
            raise ValueError("No data available for analysis. Run fetch first.")

        self.last_analysis = self.analyzer.analyze_all()
        logger.info("Analysis complete")

        return self.last_analysis

    def get_recent_activities(self) -> list:
        """Get recent activities for training plan context."""
        activities_dir = self.data_dir / "activities"
        activities = []

        if activities_dir.exists():
            for filepath in sorted(activities_dir.glob("*.json"), reverse=True)[:10]:
                try:
                    with open(filepath) as f:
                        activities.append(json.load(f))
                except (json.JSONDecodeError, IOError):
                    continue

        return activities

    def generate_training_plan(self, analysis_results: Optional[dict] = None) -> dict:
        """Generate AI-powered training plan (requires API key)."""
        self._init_ai_coach(require_api=True)

        if analysis_results is None:
            if self.last_analysis is None:
                self.run_analysis()
            analysis_results = self.last_analysis

        recent_activities = self.get_recent_activities()

        logger.info("Generating AI training plan...")
        self.last_training_plan = self.ai_coach.generate_training_plan(
            self.user_config,
            analysis_results,
            recent_activities
        )
        logger.info("Training plan generated")

        return self.last_training_plan

    def prepare_for_claude_code(self, analysis_results: Optional[dict] = None) -> Path:
        """
        Prepare context file for Claude Code to generate training plan.

        Use this when no Anthropic API key is available (enterprise users).
        Claude Code will read this context and generate the plan directly.

        Returns:
            Path to the context file
        """
        self._init_ai_coach()

        if analysis_results is None:
            if self.last_analysis is None:
                self.run_analysis()
            analysis_results = self.last_analysis

        recent_activities = self.get_recent_activities()

        logger.info("Preparing context for Claude Code...")
        context_path = self.ai_coach.prepare_context(
            self.user_config,
            analysis_results,
            recent_activities
        )
        logger.info(f"Context saved to: {context_path}")

        return context_path

    def load_training_plan(self, plan_path: Path) -> dict:
        """Load a training plan from a JSON file (generated by Claude Code)."""
        with open(plan_path, 'r') as f:
            self.last_training_plan = json.load(f)
        return self.last_training_plan

    def save_training_plan(self, training_plan: dict, output_path: Optional[Path] = None) -> Path:
        """Save training plan to a JSON file."""
        if output_path is None:
            output_path = self.data_dir / "training_plan.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(training_plan, f, indent=2)

        self.last_training_plan = training_plan
        return output_path

    def generate_email(
        self,
        analysis_results: Optional[dict] = None,
        training_plan: Optional[dict] = None
    ) -> dict:
        """Generate email content."""
        if analysis_results is None:
            analysis_results = self.last_analysis
        if training_plan is None:
            training_plan = self.last_training_plan

        if analysis_results is None or training_plan is None:
            raise ValueError("Must run analysis and generate training plan first")

        logger.info("Generating email content...")
        self.last_email = self.email_generator.generate_email(
            self.user_config.to_dict(),
            analysis_results,
            training_plan
        )
        logger.info("Email content generated")

        return self.last_email

    def save_email_for_mcp(self, email_content: Optional[dict] = None) -> Path:
        """
        Save email content to a file for the Gmail MCP to send.

        The MCP server will read this file and send the email.

        Args:
            email_content: Email dict with 'subject' and 'html_body'

        Returns:
            Path to the saved email file
        """
        if email_content is None:
            email_content = self.last_email

        if email_content is None:
            raise ValueError("No email content to save")

        # Create output directory
        output_dir = self.data_dir / "email_queue"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save email with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        email_file = output_dir / f"weekly_report_{timestamp}.json"

        email_data = {
            "to": self.user_config.email,
            "subject": email_content["subject"],
            "html_body": email_content["html_body"],
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        }

        with open(email_file, 'w') as f:
            json.dump(email_data, f, indent=2)

        logger.info(f"Email saved to: {email_file}")
        return email_file

    def generate_full_report(
        self,
        fetch_data: bool = True,
        days: int = 14,
        use_mcp: bool = False,
        training_plan: Optional[dict] = None
    ) -> dict:
        """
        Generate a complete weekly report.

        Args:
            fetch_data: Whether to fetch fresh Garmin data
            days: Number of days of data to fetch
            use_mcp: Whether MCP servers are being used
            training_plan: Pre-generated training plan (for Claude Code workflow)

        Returns:
            Dictionary with analysis, training_plan, and email content
        """
        logger.info("=" * 50)
        logger.info("Starting weekly report generation")
        logger.info("=" * 50)

        # Step 1: Fetch data (if requested)
        if fetch_data:
            if not self.fetch_garmin_data(days=days, use_mcp=use_mcp):
                if not self._verify_data_exists():
                    raise RuntimeError("No Garmin data available")
                logger.warning("Using existing cached data")

        # Step 2: Run analysis
        analysis = self.run_analysis()

        # Step 3: Get training plan (either provided or generate)
        if training_plan is not None:
            self.last_training_plan = training_plan
            logger.info("Using provided training plan")
        elif os.getenv("ANTHROPIC_API_KEY"):
            training_plan = self.generate_training_plan(analysis)
        else:
            # No API key - prepare context for Claude Code
            context_path = self.prepare_for_claude_code(analysis)
            raise RuntimeError(
                f"No Anthropic API key available. Context saved to: {context_path}\n"
                "Use Claude Code to generate the training plan, then call:\n"
                "  generator.generate_full_report(training_plan=<plan_dict>)"
            )

        # Step 4: Generate email
        email = self.generate_email(analysis, training_plan)

        # Step 5: Save email for sending
        email_file = self.save_email_for_mcp(email)

        logger.info("=" * 50)
        logger.info("Weekly report generation complete")
        logger.info(f"Email saved to: {email_file}")
        logger.info("=" * 50)

        return {
            "analysis": analysis,
            "training_plan": training_plan,
            "email": email,
            "email_file": str(email_file)
        }

    def prepare_analysis_only(
        self,
        fetch_data: bool = True,
        days: int = 14,
        use_mcp: bool = False
    ) -> dict:
        """
        Run data fetch and analysis, prepare context for Claude Code.

        This is the first step in the Claude Code workflow for enterprise users.
        After calling this, Claude Code should generate the training plan,
        then call complete_report() with the plan.

        Returns:
            Dictionary with analysis and context_file path
        """
        logger.info("Preparing analysis for Claude Code workflow...")

        # Fetch data if requested
        if fetch_data:
            if not self.fetch_garmin_data(days=days, use_mcp=use_mcp):
                if not self._verify_data_exists():
                    raise RuntimeError("No Garmin data available")

        # Run analysis
        analysis = self.run_analysis()

        # Prepare context for Claude Code
        context_path = self.prepare_for_claude_code(analysis)

        return {
            "analysis": analysis,
            "context_file": str(context_path),
            "user_config": self.user_config.to_dict()
        }

    def complete_report(self, training_plan: dict) -> dict:
        """
        Complete the report with a training plan generated by Claude Code.

        This is the second step in the Claude Code workflow.

        Args:
            training_plan: Training plan dict generated by Claude Code

        Returns:
            Dictionary with email content and file path
        """
        if self.last_analysis is None:
            raise RuntimeError("No analysis available. Run prepare_analysis_only() first.")

        self.last_training_plan = training_plan

        # Generate email
        email = self.generate_email(self.last_analysis, training_plan)

        # Save email for sending
        email_file = self.save_email_for_mcp(email)

        return {
            "analysis": self.last_analysis,
            "training_plan": training_plan,
            "email": email,
            "email_file": str(email_file)
        }

    def get_preview_text(self) -> str:
        """Get plain text preview of the last generated plan."""
        if self.last_training_plan is None:
            return "No training plan generated yet"

        return self.email_generator.generate_preview_text(self.last_training_plan)


def run_weekly_report(
    fetch_data: bool = True,
    days: int = 14,
    preview_only: bool = False,
    use_mcp: bool = False
) -> dict:
    """
    Main entry point for generating and optionally sending the weekly report.

    Args:
        fetch_data: Whether to fetch fresh Garmin data
        days: Number of days to fetch
        preview_only: If True, generate but don't save/send
        use_mcp: Whether to use MCP servers

    Returns:
        Report data dictionary
    """
    generator = WeeklyReportGenerator()

    # Check if user is configured
    if not generator.user_config.is_configured():
        logger.warning("User not configured. Run 'python main.py email setup' first.")

    # Generate report
    result = generator.generate_full_report(
        fetch_data=fetch_data,
        days=days,
        use_mcp=use_mcp
    )

    if preview_only:
        # Print preview to console
        print("\n" + generator.get_preview_text())

    return result


# For direct execution (e.g., from launchd)
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate weekly training report")
    parser.add_argument("--no-fetch", action="store_true", help="Skip data fetch, use cached data")
    parser.add_argument("--days", type=int, default=14, help="Days of data to fetch")
    parser.add_argument("--preview", action="store_true", help="Preview only, don't send")

    args = parser.parse_args()

    try:
        result = run_weekly_report(
            fetch_data=not args.no_fetch,
            days=args.days,
            preview_only=args.preview
        )

        if not args.preview:
            print(f"\nReport generated successfully!")
            print(f"Email file: {result['email_file']}")
            print(f"\nTo send via Gmail MCP, use Claude Code with:")
            print(f"  'Send the email at {result['email_file']}'")

    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        sys.exit(1)
