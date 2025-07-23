from pathlib import Path
from dotenv import load_dotenv
import os
import logging

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

CRUNCHBASE_KEY = os.getenv("CRUNCHBASE_API_KEY")
ZAPIER_WEBHOOK_URL = os.getenv("ZAPIER_WEBHOOK_URL")
VC_FIRM_NAMES = [n.strip() for n in os.getenv("VC_FIRM_NAMES", "").split(",") if n.strip()]
CACHE_PATH = ROOT / "vc_uuid_cache.json"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
