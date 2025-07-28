import logging
import requests
from typing import List
import time

from .config import ZAPIER_WEBHOOK_URL
from .models import InvestmentDeal

_log = logging.getLogger(__name__)

class ZapierClient:
    def send_deals(self, deals: List[InvestmentDeal]) -> None:
        if not deals:
            _log.info("No deals to send – skipping webhook.")
            return
        for idx, deal in enumerate(deals, 1):
            payload = deal.__dict__  # flat JSON for Zapier/Clay mapping
            try:
                resp = requests.post(ZAPIER_WEBHOOK_URL, json=payload, timeout=30)
                resp.raise_for_status()
                _log.info("[%d/%d] Sent %s", idx, len(deals), deal.company_name)
            except Exception as e:
                _log.error("[%d/%d] Failed %s: %s", idx, len(deals), deal.company_name, str(e))
            time.sleep(1.0)  # slower pacing for Zapier
        _log.info("Finished sending %d deals", len(deals))
