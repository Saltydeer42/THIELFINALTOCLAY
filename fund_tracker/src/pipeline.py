"""
End‑to‑end orchestration: Crunchbase → Zapier.
"""

import logging
from itertools import chain
from typing import List

from .config import VC_FIRM_NAMES
from .crunchbase_client import CrunchbaseClient
from .uuid_cache import UuidCache
from .zapier_client import ZapierClient
from .models import InvestmentDeal

_log = logging.getLogger(__name__)

def run_pipeline() -> List[InvestmentDeal]:
    cache = UuidCache()
    cb = CrunchbaseClient(cache)
    zap = ZapierClient()

    all_deals: List[InvestmentDeal] = list(
        chain.from_iterable(cb.get_recent_deals(name) for name in VC_FIRM_NAMES)
    )

    # Deduplicate (same company may appear twice if >1 VC in round)
    unique: dict[str, InvestmentDeal] = {}
    for d in all_deals:
        key = (d.company_name, d.announced_date)
        if key not in unique:
            unique[key] = d
    deduped = list(unique.values())

    zap.send_deals(deduped)
    return deduped
