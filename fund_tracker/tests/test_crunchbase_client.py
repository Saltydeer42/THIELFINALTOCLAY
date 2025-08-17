import pendulum
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.crunchbase_client import CrunchbaseClient
from src.uuid_cache import UuidCache

def test_get_recent_deals(rm, tmp_path):
    cache = UuidCache(tmp_path / "cache.json")
    cache._store["VC"] = "uuid‑vc"
    since = pendulum.now().subtract(days=7).to_date_string()

    rm.post(
        "https://api.crunchbase.com/v4/data/searches/funding_rounds",
        json={
            "entities": [
                {
                    "properties": {
                        "organization_identifier": {
                            "value": "Acme",
                            "permalink": "acme-co",
                        },
                        "announced_on": pendulum.now().to_date_string(),
                        "investment_type": "Seed",
                        "money_raised": {"value": 5000000},
                    }
                }
            ]
        },
    )
    cb = CrunchbaseClient(cache)
    deals = cb.get_recent_deals("VC", days_back=7)

    assert rm.last_request.json() == {
        "field_ids": [
            "investment_type", "announced_on", "money_raised",
            "investor_organization_identifier", "investor_identifier",
            "funded_organization_identifier", "organization_identifier"
        ],
        "order": [{"field_id": "announced_on", "sort": "desc"}],
        "query": [
            {
                "type": "predicate",
                "field_id": "investor_organization_identifier",
                "operator_id": "includes",
                "values": ["uuid‑vc"],
            },
            {
                "type": "predicate",
                "field_id": "investor_identifier",
                "operator_id": "includes",
                "values": ["uuid‑vc"],
            },
            {
                "type": "predicate",
                "field_id": "announced_on",
                "operator_id": "gte",
                "values": [since],
            }
        ],
    }
    assert len(deals) == 1
    d = deals[0]
    assert d.company_name == "Acme"
    assert d.amount_usd == 5000000
