# Self‑Updating VC Fund Tracker

A single command (or scheduled GitHub Action) pulls the previous week’s
funding rounds for ~70 VC funds, deduplicates the list, and posts a JSON
payload to Zapier, where your Clay enrichment Zap takes over.

## Quick start (local)

```bash
git clone <repo> && cd fund_tracker
cp .env.example .env         # insert real keys
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest          # run tests
python -m fund_tracker.cli   # one‑off run
