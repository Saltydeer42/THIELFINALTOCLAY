"""
Command‑line entry point.

`python -m fund_tracker.cli` will execute the pipeline
and print the deals pushed to Zapier.
"""

import json
from .pipeline import run_pipeline

def main() -> None:
    deals = run_pipeline()
    print(json.dumps([d.__dict__ for d in deals], indent=2))

if __name__ == "__main__":
    main()
