#!/usr/bin/env python3
"""CLI entrypoint: triage a batch of Alertmanager alerts and print a report.

Usage:
    python cli.py sample_data/sample_alerts.json
    python cli.py sample_data/sample_alerts.json --out report.md
"""

import argparse
import sys

from triage_agent import TriageAgent, load_alerts_from_file, render_markdown_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Triage Alertmanager alerts with Claude.")
    parser.add_argument("alerts_file", help="Path to a JSON file with an Alertmanager-style payload")
    parser.add_argument("--out", help="Write the Markdown report to this file instead of stdout")
    parser.add_argument("--model", default="claude-sonnet-4-6", help="Model to use (provider-specific)")
    parser.add_argument("--provider", default="anthropic", help="Model provider to use: anthropic (Claude) or openai")
    args = parser.parse_args()

    alerts = load_alerts_from_file(args.alerts_file)
    if not alerts:
        print("No alerts found in input file.", file=sys.stderr)
        return 1

    agent = TriageAgent(model=args.model, provider=args.provider)
    results = agent.triage_batch(alerts)
    report = render_markdown_report(results)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report written to {args.out}")
    else:
        print(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
