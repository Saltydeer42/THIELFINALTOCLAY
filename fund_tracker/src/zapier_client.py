import logging
import time
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
        sent = 0
        for deal in deals:
            payload = deal.__dict__
            resp = requests.post(ZAPIER_WEBHOOK_URL, json=payload, timeout=30)
            try:
                resp.raise_for_status()
                sent += 1
                _log.info("Sent deal to Zapier: %s – %s", deal.company_name, deal.announced_date)
            finally:
                # Zapier pacing
                time.sleep(1)
        _log.info("Sent %d/%d deals to Zapier", sent, len(deals))
