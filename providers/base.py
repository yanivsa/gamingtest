"""
Base Provider Adapter Interface and Health Data Structures.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo('Asia/Jerusalem')


class BaseProviderAdapter:
    """
    Abstract base class for all family travel provider adapters.
    """
    name: str = "base_adapter"
    provider_type: str = "flight"  # flight | hotel | package | discovery
    required_secrets: List[str] = []

    def __init__(self, secrets: Optional[Dict[str, str]] = None):
        self.secrets = secrets or {}

    def get_missing_secrets(self) -> List[str]:
        return [s for s in self.required_secrets if not self.secrets.get(s, "").strip()]

    def check_health(self) -> Dict[str, Any]:
        """
        Returns health status dict with status: ok | missing_credentials | degraded | error
        """
        missing = self.get_missing_secrets()
        now_iso = datetime.now(TZ).isoformat()
        if missing:
            return {
                "provider": self.name,
                "type": self.provider_type,
                "status": "missing_credentials",
                "message": f"Missing required secrets: {', '.join(missing)}",
                "missing_secrets": missing,
                "checked_at": now_iso
            }
        return {
            "provider": self.name,
            "type": self.provider_type,
            "status": "ok",
            "message": "Configured and operational",
            "checked_at": now_iso
        }

    def search_flights(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []

    def search_hotels(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []

    def search_packages(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        return []
