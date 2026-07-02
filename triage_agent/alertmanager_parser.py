"""Parsing helpers for Prometheus Alertmanager webhook payloads."""

import json
from pathlib import Path

from .models import Alert


def parse_alertmanager_webhook(payload: dict) -> list[Alert]:
    """Convert a raw Alertmanager webhook payload into a list of Alert objects.

    Alertmanager webhooks send a batch under the 'alerts' key. See:
    https://prometheus.io/docs/alerting/latest/configuration/#webhook_config
    """
    raw_alerts = payload.get("alerts", [])
    return [Alert.from_alertmanager_payload(raw) for raw in raw_alerts]


def load_alerts_from_file(path: str | Path) -> list[Alert]:
    """Load and parse alerts from a JSON file on disk (for local testing/demos)."""
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return parse_alertmanager_webhook(payload)
