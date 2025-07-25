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
    ORG = "https://api.crunchbase.com/v4/data/entities/organizations/{}"

    def __init__(self, uuid_cache: UuidCache):
        self.cache = uuid_cache
        self._org_cache: dict[str, str | None] = {}

    def _get_website(self, org_uuid: str) -> str | None:
        """Return the organization's website URL (cached)."""
        if org_uuid in self._org_cache:
            return self._org_cache[org_uuid]
        url = self.ORG.format(org_uuid)
        params = {"user_key": CRUNCHBASE_KEY, "field_ids": "website"}
        try:
            resp = requests.get(url, params=params, timeout=20)
            resp.raise_for_status()
            props = resp.json().get("properties", {})
            website = (
                props.get("homepage_url")
                or props.get("website")
                or props.get("website_url")
            )
            if website:
                _log.debug("Website for %s: %s", org_uuid, website)
        except Exception as e:
            _log.warning("Website lookup failed for %s: %s", org_uuid, e)
            website = None
        self._org_cache[org_uuid] = website
        return website

    def _search_body(self, investor_id: str, since_iso: str) -> dict:
        """Return the JSON body for the Search API POST."""
        return {
            "field_ids": [
                "identifier",
                "announced_on",
                "funded_organization_identifier",
                "money_raised",
                "investment_type",
                "investor_identifiers"
            ],
            "order": [{"field_id": "announced_on", "sort": "desc"}],
            "query": [
                {
                    "type": "predicate",
                    "field_id": "investor_identifiers",
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
            org = row["properties"]["funded_organization_identifier"]
            website = self._get_website(org["uuid"]) or self._get_website(org["permalink"])
            deals.append(
                InvestmentDeal(
                    vc_name=vc_name,
                    company_name=org["value"],
                    announced_date=row["properties"]["announced_on"],
                    round_type=row["properties"]["investment_type"],
                    amount_usd=row["properties"].get("money_raised", {"value": None})["value"],
                    crunchbase_url=f'https://www.crunchbase.com/organization/{org["permalink"]}',
                    company_url=website,
                )
            )
        _log.info("%s – fetched %d deals", vc_name, len(deals))
        return deals
