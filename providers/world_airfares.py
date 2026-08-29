"""
World Airfares Provider Adapter
Primary live flight verification adapter.
"""
import os, json, urllib.request
from typing import Dict, List, Any, Optional
from .base import BaseProviderAdapter


class WorldAirfaresAdapter(BaseProviderAdapter):
    name = "world_airfares"
    provider_type = "flight"
    required_secrets = ["WORLD_AIRFARES_API_KEY"]

    def __init__(self, secrets: Optional[Dict[str, str]] = None):
        if secrets is None:
            secrets = {
                "WORLD_AIRFARES_API_KEY": os.getenv("WORLD_AIRFARES_API_KEY", "").strip(),
                "WORLD_AIRFARES_URL": os.getenv("WORLD_AIRFARES_URL", "").strip(),
            }
        super().__init__(secrets)

    def search_flights(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search or verify flights for passengers (2 adults + 3 children: 10, 7, 2).
        If API URL or API Key is provided, performs live fetch, otherwise returns empty/health status.
        """
        missing = self.get_missing_secrets()
        url = self.secrets.get("WORLD_AIRFARES_URL")
        if missing and not url:
            return []

        # If live URL endpoint configured
        endpoint = url or "https://api.worldairfares.com/v1/search"
        try:
            req = urllib.request.Request(
                endpoint,
                headers={
                    "User-Agent": "family-travel-monitor/1.0",
                    "X-Api-Key": self.secrets.get("WORLD_AIRFARES_API_KEY", ""),
                    "Content-Type": "application/json"
                },
                data=json.dumps(params).encode('utf-8') if params else None
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data.get("flights", []) if isinstance(data, dict) else []
        except Exception as e:
            return []
