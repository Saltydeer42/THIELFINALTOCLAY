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

    def _search_body(self, investor_id: str, since_iso: str, investor_field: str = "investor_identifiers") -> dict:
        """Return the JSON body for the Search API POST."""
        return {
            "field_ids": [
                "investment_type",
                "announced_on",
                "money_raised_usd",
                investor_field,
                "funded_organization_identifier",
                "organization_identifier",
            ],
            "order": [{"field_id": "announced_on", "sort": "desc"}],
            "query": [
                {
                    "type": "predicate",
                    "field_id": investor_field,
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
        params = {"user_key": CRUNCHBASE_KEY}

        rows = []
        last_error_text = None
        for field in ("investor_identifiers", "investor_organization_identifier", "investor_identifier"):
            body = self._search_body(vc_uuid, since, investor_field=field)
            resp = requests.post(self.BASE, params=params, json=body, timeout=30)
            if resp.status_code >= 400:
                last_error_text = resp.text
                continue
            resp.raise_for_status()
            rows = resp.json().get("entities", [])
            break
        if not rows and last_error_text:
            _log.error("Crunchbase search failed for %s: %s", vc_name, last_error_text)

        deals: List[InvestmentDeal] = []
        for row in rows:
            props = row.get("properties", {})
            org = (
                props.get("funded_organization_identifier")
                or props.get("organization_identifier")
            )
            if org is None:
                continue
            amount = props.get("money_raised_usd")
            if amount is None and isinstance(props.get("money_raised"), dict):
                amount = props.get("money_raised", {}).get("value")
            deals.append(
                InvestmentDeal(
                    vc_name=vc_name,
                    company_name=org["value"],
                    announced_date=props["announced_on"],
                    round_type=props["investment_type"],
                    amount_usd=amount,
                    crunchbase_url=f'https://www.crunchbase.com/organization/{org["permalink"]}',
                )
            )
        _log.info("%s – fetched %d deals", vc_name, len(deals))
        return deals
