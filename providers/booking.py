"""
Booking.com Provider Adapter
Primary hotel verification adapter.
"""
import os, json, urllib.request
from typing import Dict, List, Any, Optional
from .base import BaseProviderAdapter


class BookingComAdapter(BaseProviderAdapter):
    name = "booking"
    provider_type = "hotel"
    required_secrets = ["BOOKING_API_KEY"]

    def __init__(self, secrets: Optional[Dict[str, str]] = None):
        if secrets is None:
            secrets = {
                "BOOKING_API_KEY": os.getenv("BOOKING_API_KEY", "").strip(),
                "BOOKING_AFFILIATE_ID": os.getenv("BOOKING_AFFILIATE_ID", "").strip(),
            }
        super().__init__(secrets)

    def search_hotels(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        missing = self.get_missing_secrets()
        if missing:
            return []

        endpoint = "https://api.booking.com/v1/hotels/search"
        try:
            req = urllib.request.Request(
                endpoint,
                headers={
                    "User-Agent": "family-travel-monitor/1.0",
                    "X-Api-Key": self.secrets.get("BOOKING_API_KEY", ""),
                    "Content-Type": "application/json"
                },
                data=json.dumps(params).encode('utf-8') if params else None
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return data.get("hotels", []) if isinstance(data, dict) else []
        except Exception:
            return []
