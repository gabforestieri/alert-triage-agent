"""Unit tests for the triage agent. The Claude API call is mocked, so these
run with no network access and no API key."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from triage_agent import Alert, Severity, TriageAgent
from triage_agent.alertmanager_parser import parse_alertmanager_webhook
from triage_agent.report import render_markdown_report


SAMPLE_PAYLOAD = {
    "alerts": [
        {
            "labels": {"alertname": "HighErrorRate", "service": "udis-api", "severity": "critical"},
            "annotations": {"summary": "Error rate high", "description": "5xx rate above threshold"},
            "startsAt": "2026-07-02T14:02:00Z",
        }
    ]
}

FAKE_MODEL_RESPONSE = {
    "assessed_severity": "critical",
    "probable_cause": "Recent deploy introduced a regression causing 5xx errors.",
    "recommended_action": "Roll back rev a1b2c3d and check error logs for stack traces.",
    "is_actionable_now": True,
    "reasoning": "Error rate spike correlates directly with a recent deploy timestamp.",
}


def _mock_anthropic_response(payload: dict):
    block = MagicMock()
    block.type = "text"
    block.text = json.dumps(payload)
    response = MagicMock()
    response.content = [block]
    return response


def test_parse_alertmanager_webhook():
    alerts = parse_alertmanager_webhook(SAMPLE_PAYLOAD)
    assert len(alerts) == 1
    assert alerts[0].alert_name == "HighErrorRate"
    assert alerts[0].service == "udis-api"
    assert alerts[0].severity_label == "critical"


@patch("triage_agent.llm.anthropic.Anthropic")
def test_triage_returns_structured_result(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_anthropic_response(FAKE_MODEL_RESPONSE)
    mock_anthropic_cls.return_value = mock_client

    agent = TriageAgent(api_key="fake-key-for-tests")
    alert = Alert(
        alert_name="HighErrorRate",
        service="app-api",
        severity_label="critical",
        summary="Error rate high",
        description="5xx rate above threshold",
    )

    result = agent.triage(alert)

    assert result.assessed_severity == Severity.CRITICAL
    assert result.is_actionable_now is True
    assert "rollback" in result.recommended_action.lower() or "roll back" in result.recommended_action.lower()
    mock_client.messages.create.assert_called_once()


@patch("triage_agent.llm.anthropic.Anthropic")
def test_triage_handles_malformed_json_gracefully(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _mock_anthropic_response({})
    mock_client.messages.create.return_value.content[0].text = "not valid json at all"
    mock_anthropic_cls.return_value = mock_client

    agent = TriageAgent(api_key="fake-key-for-tests")
    alert = Alert(
        alert_name="Test",
        service="test-service",
        severity_label="low",
        summary="",
        description="",
    )

    result = agent.triage(alert)
    assert result.assessed_severity == Severity.UNKNOWN


def test_render_markdown_report_orders_by_severity():
    from triage_agent.models import TriageResult

    low = TriageResult(
        alert=Alert("A", "svc-a", "low", "", ""),
        assessed_severity=Severity.LOW,
        probable_cause="x", recommended_action="y", is_actionable_now=False, reasoning="z",
    )
    critical = TriageResult(
        alert=Alert("B", "svc-b", "critical", "", ""),
        assessed_severity=Severity.CRITICAL,
        probable_cause="x", recommended_action="y", is_actionable_now=True, reasoning="z",
    )

    report = render_markdown_report([low, critical])
    assert report.index("svc-b") < report.index("svc-a")
