import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.uuid_cache import UuidCache

def test_cache_roundtrip(tmp_path, rm):
    path = tmp_path / "cache.json"
    rm.get(
        "https://api.crunchbase.com/v4/data/autocompletes",
        json={"entities": [{"uuid": "123", "permalink": "dummy"}]},
    )
    cache = UuidCache(path)
    assert cache.get_uuid("Test VC") == "123"
    # second call hits local cache, no HTTP
    assert cache.get_uuid("Test VC") == "123"
