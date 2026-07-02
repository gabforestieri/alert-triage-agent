# alert-triage-agent

A minimal SRE triage agent that takes Prometheus Alertmanager alerts and uses
Claude to assess severity, hypothesize a probable cause, and recommend a next
action — producing a prioritized Markdown report an on-call engineer can act
on in seconds instead of reading raw alert payloads.

## Why

Alert fatigue is a real operational cost: on-call engineers spend meaningful
time just figuring out *which* firing alert to look at first. This project is
a small proof of concept for closing that gap with an LLM-based triage step
that sits between Alertmanager and the human — read-only, no auto-remediation.

## How it works

1. Alertmanager (or a saved webhook payload) provides a batch of firing alerts.
2. Each alert is normalized into an `Alert` object (`alertmanager_parser.py`).
3. `TriageAgent` sends each alert's context to a model provider (Claude/Anthropic or GPT/OpenAI)
   with a system prompt constraining the response to structured JSON (severity, probable cause,
   recommended action, whether it's actionable right now, reasoning).
4. Results are sorted by assessed severity and rendered into a Markdown report.

```
Alertmanager webhook → Alert (normalized) → TriageAgent (LLM Provider) → TriageResult → Markdown report
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # add ANTHROPIC_API_KEY and/or OPENAI_API_KEY
export $(cat .env | xargs)
```

### Supported Providers

- **Anthropic (Claude)** — set `ANTHROPIC_API_KEY` in `.env`
- **OpenAI (GPT)** — set `OPENAI_API_KEY` in `.env`

## Usage

Triage with default Claude model (Anthropic):

```bash
python cli.py sample_data/sample_alerts.json
```

Triage with OpenAI (GPT-4):

```bash
python cli.py sample_data/sample_alerts.json --provider openai --model gpt-4
```

Write the report to a file instead of stdout:

```bash
python cli.py sample_data/sample_alerts.json --out report.md
```

### CLI options

- `--provider` — `anthropic` (default) or `openai`
- `--model` — Model identifier (e.g., `claude-sonnet-4-6` for Anthropic, `gpt-4o` for OpenAI)

## Tests

The Claude API call is mocked in tests, so no API key or network access is
required to run them:

```bash
pytest tests/ -v
```

## Project structure

```
alert-triage-agent/
├── cli.py                       # entrypoint
├── triage_agent/
│   ├── models.py                 # Alert / TriageResult / Severity
│   ├── alertmanager_parser.py    # webhook payload -> Alert objects
│   ├── agent.py                  # LLM triage + structured parsing
│   ├── llm.py                    # Multi-provider LLM abstraction (Anthropic, OpenAI)
│   └── report.py                 # Markdown report rendering
├── sample_data/sample_alerts.json
├── tests/test_agent.py
└── .github/workflows/ci.yml      # GitHub Actions CI (test on Python 3.10+)
```

## Possible next steps

- Wire the CLI into an actual Alertmanager webhook receiver (Flask/FastAPI)
  instead of reading from a file.
- Push the rendered report to Slack or PagerDuty as an incident note.
- Add a feedback loop: let on-call engineers mark triage results as
  correct/incorrect to track the agent's accuracy over time.
- Swap the file-based prompt for tool use, giving Claude read access to
  Grafana/Prometheus queries to pull real-time context before triaging.

## Disclaimer

This is a learning/portfolio project built to explore AI-assisted SRE
tooling. It is not connected to, and does not use data from, any employer's
production systems.
