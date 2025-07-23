import pendulum
from src.crunchbase_client import CrunchbaseClient
from src.uuid_cache import UuidCache

def test_get_recent_deals(rm, tmp_path):
    cache = UuidCache(tmp_path / "cache.json")
    cache._store["VC"] = "uuid‑vc"

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
                        "money_raised_usd": 5000000,
                    }
                }
            ]
        },
    )
    cb = CrunchbaseClient(cache)
    deals = cb.get_recent_deals("VC", days_back=7)
    assert len(deals) == 1
    d = deals[0]
    assert d.company_name == "Acme"
    assert d.amount_usd == 5000000
