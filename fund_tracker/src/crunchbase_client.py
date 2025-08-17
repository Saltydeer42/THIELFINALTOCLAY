import logging
import requests
import pendulum
from typing import List

from .config import CRUNCHBASE_KEY
from .models import InvestmentDeal
from .uuid_cache import UuidCache

_log = logging.getLogger(__name__)

class CrunchbaseClient:
    BASE = "https://api.crunchbase.com/v4/data/searches/funding_rounds"

    def __init__(self, uuid_cache: UuidCache):
        self.cache = uuid_cache

    def _search_body(self, investor_id: str, since_iso: str) -> dict:
        """Return the JSON body for the Search API POST."""
        return {
            "field_ids": [
                "investment_type",
                "announced_on",
                "money_raised_usd",
                "investor_organization_identifier",
                "organization_identifier"
            ],
            "order": [{"field_id": "announced_on", "sort": "desc"}],
            "query": [
                {
                    "type": "predicate",
                    "field_id": "investor_organization_identifier",
                    "operator_id": "includes",
                    "values": [investor_id]
                },
                {
                    "type": "predicate",
                    "field_id": "announced_on",
                    "operator_id": "gte",
                    "values": [since_iso]
                }
            ]
        }

    def get_recent_deals(
        self, vc_name: str, days_back: int = 7
    ) -> List[InvestmentDeal]:
        vc_uuid = self.cache.get_uuid(vc_name)
        if not vc_uuid:
            return []

        since = pendulum.now().subtract(days=days_back).to_date_string()
        body = self._search_body(vc_uuid, since)
        params = {"user_key": CRUNCHBASE_KEY}

        resp = requests.post(self.BASE, params=params, json=body, timeout=30)
        resp.raise_for_status()
        rows = resp.json().get("entities", [])

        deals: List[InvestmentDeal] = []
        for row in rows:
            org = row["properties"]["organization_identifier"]
            deals.append(
                InvestmentDeal(
                    vc_name=vc_name,
                    company_name=org["value"],
                    announced_date=row["properties"]["announced_on"],
                    round_type=row["properties"]["investment_type"],
                    amount_usd=row["properties"].get("money_raised_usd"),
                    crunchbase_url=f'https://www.crunchbase.com/organization/{org["permalink"]}',
                )
            )
        _log.info("%s – fetched %d deals", vc_name, len(deals))
        return deals
