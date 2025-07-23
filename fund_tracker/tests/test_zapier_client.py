from src.zapier_client import ZapierClient
from src.models import InvestmentDeal

def test_send_deals(rm):
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
