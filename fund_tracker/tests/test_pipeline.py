from src.pipeline import run_pipeline
from src.config import VC_FIRM_NAMES

def test_pipeline_smoke(monkeypatch, rm, tmp_path):
    # Stub UUID & funding calls for each VC in list
    uuid_counter = 0
    for name in VC_FIRM_NAMES:
        uuid_counter += 1
        rm.get(
            "https://api.crunchbase.com/v4/autocomplete/organizations",
            additional_matcher=lambda req, n=name: req.qs["query"] == [n],
            json={"entities": [{"uuid": f"id{uuid_counter}", "permalink": "p"}]},
        )
    rm.post("https://api.crunchbase.com/v4/data/searches/funding_rounds", json={"entities": []})
    rm.post("https://hooks.zapier.com/hooks/catch/TEST/123", status_code=200)
    deals = run_pipeline()
    assert deals == []
