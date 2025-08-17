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

    def _search_body(
        self,
        investor_id: str,
        since_iso: str | None,
        investor_field: str = "investor_identifiers",
        include_org_identifier: bool = True,
    ) -> dict:
        """Return the JSON body for the Search API POST."""
        query = [
            {
                "type": "predicate",
                "field_id": investor_field,
                "operator_id": "includes",
                "values": [investor_id]
            }
        ]
        if since_iso:
            query.append(
                {
                    "type": "predicate",
                    "field_id": "announced_on",
                    "operator_id": "gte",
                    "values": [since_iso]
                }
            )
        field_ids = [
            "investment_type",
            "announced_on",
            "money_raised",
            investor_field,
            "funded_organization_identifier",
        ]
        if include_org_identifier:
            field_ids.append("organization_identifier")
        return {
            "field_ids": field_ids,
            "order": [{"field_id": "announced_on", "sort": "desc"}],
            "query": query,
        }

    def _get_website(self, org_uuid: str) -> str | None:
        if org_uuid in self._org_cache:
            return self._org_cache[org_uuid]

        url = self.ORG.format(org_uuid)
        params = {"user_key": CRUNCHBASE_KEY, "field_ids": "website"}
        try:
            resp = requests.get(url, params=params, timeout=20)
            resp.raise_for_status()
            props = resp.json().get("properties", {})
            website_raw = (
                props.get("homepage_url")
                or props.get("website")
                or props.get("website_url")
            )
            website = website_raw.get("value") if isinstance(website_raw, dict) else website_raw
        except Exception as e:
            _log.warning("Website lookup failed for %s: %s", org_uuid, e)
            website = None

        self._org_cache[org_uuid] = website
        return website

    def get_recent_deals(
        self, vc_name: str, days_back: int = 7
    ) -> List[InvestmentDeal]:
        vc_uuid = self.cache.get_uuid(vc_name)
        if not vc_uuid:
            return []

        since: str | None
        if days_back is None:
            since = None
        else:
            since = pendulum.now().subtract(days=days_back).to_date_string()
        params = {"user_key": CRUNCHBASE_KEY}

        # Try with both identifiers first; on MD101 for organization_identifier, retry without it
        rows = []
        resp = requests.post(
            self.BASE,
            params=params,
            json=self._search_body(vc_uuid, since, investor_field="investor_identifiers", include_org_identifier=True),
            timeout=30,
        )
        if resp.status_code >= 400:
            error_text = resp.text
            try:
                errors = resp.json()
            except Exception:
                errors = None
            invalid_org_identifier = False
            if isinstance(errors, list):
                invalid_org_identifier = any(
                    isinstance(e, dict) and e.get("field_id") == "organization_identifier" for e in errors
                )
            if not invalid_org_identifier and "organization_identifier" not in error_text:
                _log.error("Crunchbase search failed for %s: %s", vc_name, error_text)
            if invalid_org_identifier or "organization_identifier" in error_text:
                resp2 = requests.post(
                    self.BASE,
                    params=params,
                    json=self._search_body(
                        vc_uuid, since, investor_field="investor_identifiers", include_org_identifier=False
                    ),
                    timeout=30,
                )
                if resp2.status_code >= 400:
                    _log.error("Crunchbase search failed for %s: %s", vc_name, resp2.text)
                    rows = []
                else:
                    resp2.raise_for_status()
                    rows = resp2.json().get("entities", [])
        else:
            resp.raise_for_status()
            rows = resp.json().get("entities", [])

        deals: List[InvestmentDeal] = []
        for row in rows:
            props = row["properties"]
            org = (
                props.get("funded_organization_identifier")
                or props.get("organization_identifier")
            )
            if org is None:
                continue
            # Fetch company website using org UUID; fall back to permalink if needed
            website = None
            if isinstance(org, dict):
                org_uuid = org.get("uuid") or org.get("identifier", {}).get("uuid")
                if org_uuid:
                    website = self._get_website(org_uuid)
                if website is None and org.get("permalink"):
                    # Some accounts may allow fetching by permalink as identifier
                    website = self._get_website(org["permalink"])  # cached if previously resolved
            deals.append(
                InvestmentDeal(
                    vc_name=vc_name,
                    company_name=org["value"],
                    announced_date=props["announced_on"],
                    round_type=props["investment_type"],
                    amount_usd=props.get("money_raised", {"value": None})["value"],
                    crunchbase_url=f'https://www.crunchbase.com/organization/{org["permalink"]}',
                    company_url=website,
                )
            )
        _log.info("%s – fetched %d deals", vc_name, len(deals))
        return deals
