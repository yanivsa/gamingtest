"""
Time Value Scoring, Effective Vacation Hours, and Family Value /100 Engine.
"""
from typing import Dict, Any, Tuple
from datetime import datetime, timedelta

def parse_time_to_minutes(time_str: str) -> int:
    """
    Parses "HH:MM" or "HH:MM -> HH:MM" departure time into minutes from midnight.
    """
    try:
        clean = time_str.split('→')[0].split('->')[0].strip()
        parts = clean.split(':')
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 8 * 60  # default 08:00


def score_outbound_time(outbound_str: str) -> Tuple[float, str]:
    """
    Scores outbound flight schedule:
    06:00-11:00: excellent (100)
    11:00-14:00: good (80)
    14:00-17:00: medium (60)
    after 17:00: significant penalty (30)
    before 05:30: family-comfort penalty (60)
    """
    mins = parse_time_to_minutes(outbound_str)
    if mins < 5 * 60 + 30:
        return 60.0, "לפני 05:30 (סביר - עייפות משפחתית)"
    elif 6 * 60 <= mins <= 11 * 60:
        return 100.0, "מצוין (06:00–11:00)"
    elif 11 * 60 < mins <= 14 * 60:
        return 80.0, "טוב (11:00–14:00)"
    elif 14 * 60 < mins <= 17 * 60:
        return 60.0, "בינוני (14:00–17:00)"
    else:
        return 30.0, "אחרי 17:00 (פגיעה בשעות חופשה)"


def score_return_time(return_date: str, return_str: str) -> Tuple[float, str]:
    """
    Scores return flight schedule based on return date.
    Return 2026-10-01:
      15:00-21:00: ideal (100)
      13:00-15:00: acceptable (80)
      before 12:00: penalty (40)
      after 22:00: comfort penalty (60)
    Return 2026-10-02:
      Morning only (<12:00); latest useful morning flight preferred (08:00-11:00 -> 100; 06:00-08:00 -> 85).
    """
    mins = parse_time_to_minutes(return_str)
    if return_date == '2026-10-01':
        if 15 * 60 <= mins <= 21 * 60:
            return 100.0, "אידיאלי (15:00–21:00)"
        elif 13 * 60 <= mins < 15 * 60:
            return 80.0, "מקובל (13:00–15:00)"
        elif mins < 12 * 60:
            return 40.0, "מוקדם מדי (לפני 12:00)"
        elif mins > 22 * 60:
            return 60.0, "מאוחר מדי (אחרי 22:00)"
        else:
            return 70.0, "סביר"
    else:  # 2026-10-02
        if mins >= 12 * 60:
            return 0.0, "לא חוקי לחזרה ב-2.10 (אינו בבוקר)"
        elif 8 * 60 <= mins <= 11 * 60 + 30:
            return 100.0, "בוקר אופטימלי"
        elif 6 * 60 <= mins < 8 * 60:
            return 85.0, "בוקר מוקדם"
        else:
            return 70.0, "בוקר לפנות שחר"


def calculate_effective_vacation_hours(
    departure_date: str,
    outbound_str: str,
    return_date: str,
    return_str: str,
    flight_duration_hours: float = 1.5,
    transfer_hours: float = 1.0
) -> int:
    """
    Calculates approximate effective_vacation_hours at destination.
    From estimated hotel arrival until estimated leave-for-airport time.
    """
    try:
        dep_dt = datetime.strptime(departure_date, "%Y-%m-%d")
        ret_dt = datetime.strptime(return_date, "%Y-%m-%d")

        out_mins = parse_time_to_minutes(outbound_str)
        ret_mins = parse_time_to_minutes(return_str)

        # Outbound departure time
        out_time = dep_dt + timedelta(minutes=out_mins)
        # Estimated hotel arrival: departure + flight duration + transfer/immigration (1.5h)
        hotel_arrival = out_time + timedelta(hours=flight_duration_hours + transfer_hours)

        # Return flight time
        ret_time = ret_dt + timedelta(minutes=ret_mins)
        # Estimated leave hotel for airport: return departure - 2.5h (checkin + transfer)
        leave_hotel = ret_time - timedelta(hours=2.5)

        diff = leave_hotel - hotel_arrival
        hours = int(max(0, diff.total_seconds() / 3600.0))
        return hours
    except Exception:
        # Fallback default estimate
        days = 4 if return_date == '2026-10-02' else 3
        return days * 22


def calculate_family_value(deal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates Family Value / 100 score and Time Value description.
    Weights:
      30% price/value
      20% hotel/location
      15% flights (>=50% driven by time value)
      15% child fit
      10% weather/season
      5% baggage/meals/transfers
      5% flexibility/risk
    """
    out_score, out_desc = score_outbound_time(deal.get("outbound", ""))
    ret_score, ret_desc = score_return_time(deal.get("return_date", "2026-10-01"), deal.get("return", ""))

    time_value_score = (out_score + ret_score) / 2.0
    if time_value_score >= 90:
        time_value_text = "מצוין"
    elif time_value_score >= 75:
        time_value_text = "טוב"
    elif time_value_score >= 60:
        time_value_text = "בינוני"
    else:
        time_value_text = "סביר"

    # 1. Price/Value Score (30%)
    total_ils = float(deal.get("total_ils", 10000))
    if total_ils <= 7500:
        price_score = 100.0
    elif total_ils <= 10000:
        price_score = 95.0 - (total_ils - 7500) / 2500.0 * 15.0  # 95 -> 80
    elif total_ils <= 12000:
        price_score = 80.0 - (total_ils - 10000) / 2000.0 * 15.0  # 80 -> 65
    elif total_ils <= 15000:
        price_score = 65.0 - (total_ils - 12000) / 3000.0 * 25.0  # 65 -> 40
    else:
        price_score = max(0.0, 40.0 - (total_ils - 15000) / 2000.0 * 20.0)

    # 2. Hotel / Location Score (20%)
    stars = int(deal.get("stars", 4))
    guest_score = float(deal.get("guest_score", 8.5))
    hotel_score = (stars / 5.0) * 40.0 + min(10.0, guest_score) * 6.0

    # 3. Flights & Time Value Score (15%) - at least half driven by Time Value
    is_direct = bool(deal.get("direct", True))
    flight_component = time_value_score * 0.6 + (100.0 if is_direct else 60.0) * 0.4

    # 4. Child Fit Score (15%)
    benefits = deal.get("family_benefits", [])
    child_score = min(100.0, 60.0 + len(benefits) * 13.3)

    # 5. Weather / Season (10%)
    dest = deal.get("destination", "")
    if any(loc in dest for loc in ["קפריסין", "כרתים", "רודוס", "יוון", "אתונה"]):
        weather_score = 98.0
    else:
        weather_score = 85.0

    # 6. Baggage / Meals / Transfers (5%)
    baggage = deal.get("baggage", "")
    baggage_score = 90.0 if "checked" in baggage.lower() or "מזוודה" in baggage else 75.0

    # 7. Flexibility / Risk (5%)
    flex_score = 85.0

    family_value = (
        price_score * 0.30 +
        hotel_score * 0.20 +
        flight_component * 0.15 +
        child_score * 0.15 +
        weather_score * 0.10 +
        baggage_score * 0.05 +
        flex_score * 0.05
    )

    eff_hours = calculate_effective_vacation_hours(
        deal.get("departure_date", "2026-09-28"),
        deal.get("outbound", "06:20 → 07:20"),
        deal.get("return_date", "2026-10-02"),
        deal.get("return", "08:20 → 09:20")
    )

    return {
        "family_value": int(round(family_value)),
        "time_value": time_value_text,
        "effective_vacation_hours": eff_hours
    }
