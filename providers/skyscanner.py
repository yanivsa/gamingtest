"""
Skyscanner Provider Adapter
Flight discovery & cross-check adapter.
"""
import os, json, urllib.request
from typing import Dict, List, Any, Optional
from .base import BaseProviderAdapter


class SkyscannerAdapter(BaseProviderAdapter):
    name = "skyscanner"
    provider_type = "flight"
    required_secrets = ["SKYSCANNER_API_KEY"]

    def __init__(self, secrets: Optional[Dict[str, str]] = None):
        if secrets is None:
            secrets = {
                "SKYSCANNER_API_KEY": os.getenv("SKYSCANNER_API_KEY", "").strip(),
            }
        super().__init__(secrets)

    def search_flights(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        missing = self.get_missing_secrets()
        if missing:
            return []
        try:
            req = urllib.request.Request(
                "https://api.skyscanner.net/v1/search",
                headers={
                    "User-Agent": "family-travel-monitor/1.0",
                    "X-Api-Key": self.secrets.get("SKYSCANNER_API_KEY", ""),
                    "Content-Type": "application/json"
                },
                data=json.dumps(params).encode('utf-8') if params else None
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data.get("flights", []) if isinstance(data, dict) else []
        except Exception:
            return []
