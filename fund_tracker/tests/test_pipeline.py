import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pipeline import run_pipeline
from src.config import VC_FIRM_NAMES
from src.models import InvestmentDeal

def test_pipeline_smoke(monkeypatch, rm, tmp_path):
    VC_FIRM_NAMES = ["Andreessen Horowitz"]
    monkeypatch.setattr("src.pipeline.VC_FIRM_NAMES", VC_FIRM_NAMES)
    monkeypatch.setattr("src.uuid_cache.CACHE_PATH", tmp_path / "cache.json")
    monkeypatch.setattr(
        "src.zapier_client.ZAPIER_WEBHOOK_URL", "https://hooks.zapier.com/hooks/catch/TEST/123"
    )

    rm.get(
        "https://api.crunchbase.com/v4/autocomplete/organizations",
        json={"entities": [{"uuid": "a16z-uuid", "name": "Andreessen Horowitz"}]},
    )
    rm.post("https://api.crunchbase.com/v4/data/searches/funding_rounds", json={"entities": []})
    rm.post("https://hooks.zapier.com/hooks/catch/TEST/123", status_code=200)
    deals = run_pipeline()
    assert len(deals) == 0
