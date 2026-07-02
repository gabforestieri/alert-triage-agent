"""Core triage agent: sends alerts to Claude and parses structured triage results."""

import json
import os

from .models import Alert, Severity, TriageResult
from .llm import LLMFactory

SYSTEM_PROMPT = """You are an SRE triage assistant. Given a single infrastructure \
alert (in Prometheus Alertmanager format), assess it and respond with ONLY a JSON \
object (no prose, no markdown fences) with exactly these fields:

{
  "assessed_severity": "critical" | "high" | "medium" | "low",
  "probable_cause": "short technical hypothis of what is likely happening",
  "recommended_action": "concrete next step for the on-call engineer",
  "is_actionable_now": true | false,
  "reasoning": "one or two sentences explaining the assessment"
}

Base your assessment on the alert name, service, labels and description. Be \
concise and concrete - this output is read by an on-call engineer under time \
pressure."""


class TriageAgent:
    """Wraps calls to a model provider to triage individual alerts."""

    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-6", provider: str = "anthropic"):
        self.client = LLMFactory.get_client(provider=provider, api_key=api_key)
        self.model = model
        self.provider = provider

    def triage(self, alert: Alert) -> TriageResult:
        alert_context = {
            "alert_name": alert.alert_name,
            "service": alert.service,
            "reported_severity": alert.severity_label,
            "summary": alert.summary,
            "description": alert.description,
            "labels": alert.labels,
        }

        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": json.dumps(alert_context, indent=2)}
            ],
        )

        text = "".join(block.text for block in response.content if block.type == "text")
        parsed = self._safe_parse_json(text)

        return TriageResult(
            alert=alert,
            assessed_severity=Severity(parsed.get("assessed_severity", "unknown")),
            probable_cause=parsed.get("probable_cause", "N/A"),
            recommended_action=parsed.get("recommended_action", "N/A"),
            is_actionable_now=bool(parsed.get("is_actionable_now", False)),
            reasoning=parsed.get("reasoning", ""),
        )

    def triage_batch(self, alerts: list[Alert]) -> list[TriageResult]:
        return [self.triage(alert) for alert in alerts]

    @staticmethod
    def _safe_parse_json(text: str) -> dict:
        cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {}
