from dataclasses import dataclass
from typing import List

@dataclass
class InvestmentDeal:
    vc_name: str
    company_name: str
    announced_date: str  # ISO‑8601
    round_type: str
    amount_usd: float | None
    crunchbase_url: str
    # Any other fields Clay might need
