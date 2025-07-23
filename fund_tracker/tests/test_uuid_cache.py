from src.uuid_cache import UuidCache

def test_cache_roundtrip(tmp_path, rm):
    path = tmp_path / "cache.json"
    rm.get(
        "https://api.crunchbase.com/v4/autocomplete/organizations",
        json={"entities": [{"uuid": "123", "permalink": "dummy"}]},
    )
    cache = UuidCache(path)
    assert cache.get_uuid("Test VC") == "123"
    # second call hits local cache, no HTTP
    assert cache.get_uuid("Test VC") == "123"
