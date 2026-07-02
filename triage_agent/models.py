"""Data models for the alert triage agent."""

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class Alert:
    """Normalized representation of an incoming alert (Alertmanager-style)."""

    alert_name: str
    service: str
    severity_label: str
    summary: str
    description: str
    labels: dict = field(default_factory=dict)
    annotations: dict = field(default_factory=dict)
    starts_at: str = ""

    @classmethod
    def from_alertmanager_payload(cls, raw: dict) -> "Alert":
        labels = raw.get("labels", {})
        annotations = raw.get("annotations", {})
        return cls(
            alert_name=labels.get("alertname", "UnknownAlert"),
            service=labels.get("service", labels.get("job", "unknown-service")),
            severity_label=labels.get("severity", "unknown"),
            summary=annotations.get("summary", ""),
            description=annotations.get("description", ""),
            labels=labels,
            annotations=annotations,
            starts_at=raw.get("startsAt", ""),
        )


@dataclass
class TriageResult:
    """Output of the AI triage step for a single alert."""

    alert: Alert
    assessed_severity: Severity
    probable_cause: str
    recommended_action: str
    is_actionable_now: bool
    reasoning: str
