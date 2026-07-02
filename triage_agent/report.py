"""Renders TriageResult objects into a human-readable Markdown report."""

from .models import TriageResult, Severity

_SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.UNKNOWN: 4,
}

_SEVERITY_EMOJI = {
    Severity.CRITICAL: "🔴",
    Severity.HIGH: "🟠",
    Severity.MEDIUM: "🟡",
    Severity.LOW: "🟢",
    Severity.UNKNOWN: "⚪",
}


def render_markdown_report(results: list[TriageResult]) -> str:
    """Build a Markdown triage report, most severe alerts first."""
    ordered = sorted(results, key=lambda r: _SEVERITY_ORDER[r.assessed_severity])

    lines = ["# Alert Triage Report", ""]
    actionable_now = [r for r in ordered if r.is_actionable_now]
    lines.append(f"**{len(results)} alerts triaged** — {len(actionable_now)} need immediate action.")
    lines.append("")

    for r in ordered:
        emoji = _SEVERITY_EMOJI[r.assessed_severity]
        lines.append(f"## {emoji} {r.alert.alert_name} — `{r.alert.service}`")
        lines.append(f"- **Assessed severity:** {r.assessed_severity.value}")
        lines.append(f"- **Actionable now:** {'Yes' if r.is_actionable_now else 'No'}")
        lines.append(f"- **Probable cause:** {r.probable_cause}")
        lines.append(f"- **Recommended action:** {r.recommended_action}")
        lines.append(f"- **Reasoning:** {r.reasoning}")
        lines.append("")

    return "\n".join(lines)
