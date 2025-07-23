"""
Lightweight local cache for VC fund UUIDs.

If the cache file doesn’t exist or lacks a VC name,
`UuidCache.get_uuid(vc_name)` performs an Autocomplete
call to Crunchbase v4 and stores the mapping.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

import requests

from .config import CRUNCHBASE_KEY, CACHE_PATH

_log = logging.getLogger(__name__)

class UuidCache:
    def __init__(self, path: Path = CACHE_PATH):
        self.path = path
        self._store: Dict[str, str] = {}
        if path.exists():
            self._store.update(json.loads(path.read_text()))

    def save(self) -> None:
        self.path.write_text(json.dumps(self._store, indent=2))

    def get_uuid(self, vc_name: str) -> Optional[str]:
        if vc_name in self._store:
            return self._store[vc_name]

        url = "https://api.crunchbase.com/v4/autocomplete/organizations"
        params = {"user_key": CRUNCHBASE_KEY, "query": vc_name}
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        hits = resp.json().get("entities", [])
        if not hits:
            _log.warning("No UUID found for %s", vc_name)
            return None
        uuid = hits[0]["uuid"]
        self._store[vc_name] = uuid
        self.save()
        return uuid
