import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.zapier_client import ZapierClient
from src.models import InvestmentDeal

def test_send_deals(rm, monkeypatch):
    monkeypatch.setattr(
        "src.zapier_client.ZAPIER_WEBHOOK_URL", "https://hooks.zapier.com/hooks/catch/TEST/123"
    )
    rm.post("https://hooks.zapier.com/hooks/catch/TEST/123", status_code=200)
    zap = ZapierClient()
    zap.send_deals(
        [
            InvestmentDeal(
                vc_name="VC",
                company_name="Acme",
                announced_date="2025-07-20",
                round_type="Seed",
                amount_usd=1_000_000,
                crunchbase_url="url",
            )
        ]
    )
    assert rm.called
