"""
BreckenWander Provider Adapter
Resort and package discovery adapter.
"""
import os, json, urllib.request
from typing import Dict, List, Any, Optional
from .base import BaseProviderAdapter


class BreckenWanderAdapter(BaseProviderAdapter):
    name = "breckenwander"
    provider_type = "package"
    required_secrets = ["BRECKENWANDER_API_KEY"]

    def __init__(self, secrets: Optional[Dict[str, str]] = None):
        if secrets is None:
            secrets = {
                "BRECKENWANDER_API_KEY": os.getenv("BRECKENWANDER_API_KEY", "").strip(),
            }
        super().__init__(secrets)

    def search_packages(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        missing = self.get_missing_secrets()
        if missing:
            return []
        try:
            req = urllib.request.Request(
                "https://api.breckenwander.com/v1/search",
                headers={
                    "User-Agent": "family-travel-monitor/1.0",
                    "X-Api-Key": self.secrets.get("BRECKENWANDER_API_KEY", ""),
                    "Content-Type": "application/json"
                },
                data=json.dumps(params).encode('utf-8') if params else None
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data.get("packages", []) if isinstance(data, dict) else []
        except Exception:
            return []
