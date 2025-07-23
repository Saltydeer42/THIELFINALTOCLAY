import logging
import requests
from typing import List

from .config import ZAPIER_WEBHOOK_URL
from .models import InvestmentDeal

_log = logging.getLogger(__name__)

class ZapierClient:
    def send_deals(self, deals: List[InvestmentDeal]) -> None:
        if not deals:
            _log.info("No deals to send – skipping webhook.")
            return
        payload = {
            "deals": [deal.__dict__ for deal in deals],
            "total": len(deals),
        }
        resp = requests.post(ZAPIER_WEBHOOK_URL, json=payload, timeout=30)
        resp.raise_for_status()
        _log.info("Sent %d deals to Zapier", len(deals))
