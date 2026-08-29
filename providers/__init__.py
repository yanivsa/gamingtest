"""
Provider Adapters Package
"""
from typing import Dict, List, Any
from .base import BaseProviderAdapter
from .world_airfares import WorldAirfaresAdapter
from .booking import BookingComAdapter
from .skyscanner import SkyscannerAdapter
from .edreams import EDreamsAdapter
from .breckenwander import BreckenWanderAdapter

ALL_ADAPTER_CLASSES = [
    WorldAirfaresAdapter,
    BookingComAdapter,
    SkyscannerAdapter,
    EDreamsAdapter,
    BreckenWanderAdapter,
]


def check_all_providers(secrets: Dict[str, str] = None) -> List[Dict[str, Any]]:
    """
    Checks health status for all registered provider adapters.
    """
    results = []
    for cls in ALL_ADAPTER_CLASSES:
        adapter = cls(secrets=secrets)
        results.append(adapter.check_health())
    return results


__all__ = [
    "BaseProviderAdapter",
    "WorldAirfaresAdapter",
    "BookingComAdapter",
    "SkyscannerAdapter",
    "EDreamsAdapter",
    "BreckenWanderAdapter",
    "check_all_providers",
    "ALL_ADAPTER_CLASSES",
]
