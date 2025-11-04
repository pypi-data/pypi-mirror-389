"""Scheduler for Drupal Aggregator using APScheduler."""
import argparse
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import subprocess
import sys
from pathlib import Path


def run_aggregator(provider: str, model: str = None, email: bool = True, days: int = 7):
    """
    Run the aggregator as a subprocess.

    Args:
        provider: AI provider name
        model: Optional model override
        email: Whether to send email
        days: Number of days to aggregate
    """
    # Use the root wrapper script
    script_dir = Path(__file__).parent.parent
    index_py = script_dir / "index.py"

    cmd = [
        sys.executable,
        str(index_py),
        "--provider", provider,
        "--days", str(days),
        "--email", "yes" if email else "no"
    ]

    if model:
        cmd.extend(["--model", model])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Aggregator run completed successfully")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Aggregator run failed with exit code {e.returncode}")
        print(e.stderr)


def main():
    """Main scheduler entry point."""
    parser = argparse.ArgumentParser(description="Schedule Drupal Aggregator runs")

    parser.add_argument("--every", choices=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
                        required=True, help="Day of week to run")
    parser.add_argument("--hour", type=int, default=9, help="Hour to run (0-23)")
    parser.add_argument("--minute", type=int, default=0, help="Minute to run (0-59)")
    parser.add_argument("--provider", default="openai", help="AI provider to use")
    parser.add_argument("--model", help="Model override")
    parser.add_argument("--email", choices=["yes", "no"], default="yes", help="Send email")
    parser.add_argument("--days", type=int, default=7, help="Number of days to aggregate")

    args = parser.parse_args()

    # Map day names to cron day_of_week values
    day_map = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }

    scheduler = BlockingScheduler()

    # Add job
    trigger = CronTrigger(
        day_of_week=day_map[args.every],
        hour=args.hour,
        minute=args.minute
    )

    scheduler.add_job(
        run_aggregator,
        trigger=trigger,
        args=[args.provider, args.model, args.email == "yes", args.days],
        id="drupal_news",
        name="Drupal Aggregator Aggregator"
    )

    print(f"Scheduler started: Will run every {args.every} at {args.hour:02d}:{args.minute:02d}")
    print(f"Provider: {args.provider}")
    print(f"Days: {args.days}")
    print(f"Email: {args.email}")
    print("\nPress Ctrl+C to stop")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\nScheduler stopped")


if __name__ == "__main__":
    main()
