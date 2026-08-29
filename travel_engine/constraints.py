"""
Hard Search Constraints & Exclusion Validation Engine for Sukkot 2026.
"""
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime

ALLOWED_DEPARTURES = {'2026-09-27', '2026-09-28'}
ALLOWED_RETURNS = {'2026-10-01', '2026-10-02'}

ALLOWED_DATE_PAIRS = {
    ('2026-09-27', '2026-10-01'),
    ('2026-09-27', '2026-10-02'),
    ('2026-09-28', '2026-10-01'),
    ('2026-09-28', '2026-10-02'),
}

EXCLUDED_KEYWORDS = (
    'turkey', 'türkiye', 'טורקיה', 'antalya', 'istanbul', 'bodrum', 'dalaman',
    'egypt', 'מצרים', 'cairo', 'sharm', 'hurghada',
    'jordan', 'ירדן', 'amman', 'aqaba',
    'uae', 'dubai', 'איחוד האמירויות', 'דובאי', 'abu dhabi',
    'qatar', 'קטר', 'doha',
    'bahrain', 'בחריין',
    'morocco', 'מרוקו', 'marrakech',
    'tunisia', 'טוניסיה',
    'lebanon', 'לבנון', 'beirut',
    'oman', 'עומאן',
    'saudi', 'ערב הסעודית', 'riyadh', 'jeddah',
    'kuwait', 'כווית'
)

SEARCH_FAMILY_SPEC = {
    "adults": 2,
    "children_ages": [10, 7, 2],
    "total_passengers": 5
}


def is_destination_excluded(destination_str: str, country_str: str = "") -> bool:
    """
    Checks if a destination or country matches the excluded Turkey / Arab countries policy.
    """
    combined = f"{destination_str} {country_str}".lower()
    return any(keyword in combined for keyword in EXCLUDED_KEYWORDS)


def is_valid_date_pair(departure_date: str, return_date: str) -> bool:
    """
    Validates whether departure and return dates match one of the exact 4 Sukkot 2026 combinations.
    """
    return (departure_date, return_date) in ALLOWED_DATE_PAIRS


def is_valid_return_schedule(return_date: str, return_time_str: str, return_morning_flag: Optional[bool] = None) -> bool:
    """
    Checks if return flight schedule satisfies rules:
    On 2026-10-02, return MUST be morning (departure < 12:00).
    """
    if return_date != '2026-10-02':
        return True

    # Parse hour if available
    if return_time_str:
        try:
            # Format e.g. "08:20 -> 09:20" or "08:20"
            dep_part = return_time_str.split('→')[0].split('->')[0].strip()
            hour = int(dep_part.split(':')[0])
            if hour >= 12:
                return False
        except Exception:
            pass

    if return_morning_flag is False:
        return False

    return True


def validate_deal_constraints(deal: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Enforces all hard constraints on a deal candidate.
    Returns (is_valid, reason).
    """
    dest = deal.get("destination", "")
    country = deal.get("country", "")
    if is_destination_excluded(dest, country):
        return False, f"Excluded destination/country detected: {dest}"

    dep = deal.get("departure_date")
    ret = deal.get("return_date")
    if not is_valid_date_pair(dep, ret):
        return False, f"Date pair ({dep} -> {ret}) is outside allowed Sukkot windows"

    ret_time = deal.get("return", "")
    ret_morn = deal.get("return_morning", True if ret == '2026-10-02' else False)
    if ret == '2026-10-02':
        if not is_valid_return_schedule(ret, ret_time, ret_morn):
            return False, "Return on 2026-10-02 must be morning departure (< 12:00)"

    flight_url = deal.get("flight_url", "")
    hotel_url = deal.get("hotel_url", "")
    if not flight_url or not hotel_url:
        return False, "Missing reproducible flight or hotel URL"

    total = float(deal.get("total_ils", 0))
    if total <= 0:
        return False, "Invalid total ILS price"

    return True, "Valid"
