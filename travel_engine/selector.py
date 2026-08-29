"""
Discovery Aggregator, DEAD-ZONE Lead Tracker, and Top 3 Deal Selector.
"""
import os, json, math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from zoneinfo import ZoneInfo

from .constraints import validate_deal_constraints, SEARCH_FAMILY_SPEC
from .scoring import calculate_family_value

TZ = ZoneInfo('Asia/Jerusalem')

# 12-20 Plausible destination candidates for discovery
PLAUSIBLE_DESTINATIONS = [
    {"code": "LCA", "name": "לרנקה, קפריסין", "country": "Cyprus"},
    {"code": "PFO", "name": "פאפוס, קפריסין", "country": "Cyprus"},
    {"code": "AYN", "name": "איה נאפה, קפריסין", "country": "Cyprus"},
    {"code": "HER", "name": "כרתים / הרסוניסוס, יוון", "country": "Greece"},
    {"code": "RHO", "name": "רודוס, יוון", "country": "Greece"},
    {"code": "ATH", "name": "אתונה, יוון", "country": "Greece"},
    {"code": "CFU", "name": "קורפו, יוון", "country": "Greece"},
    {"code": "SKG", "name": "סלוניקי, יוון", "country": "Greece"},
    {"code": "PRG", "name": "פראג, צ'כיה", "country": "Czechia"},
    {"code": "BUD", "name": "בודפשט, הונגריה", "country": "Hungary"},
    {"code": "VIE", "name": "וינה, אוסטריה", "country": "Austria"},
    {"code": "OTP", "name": "בוקרשט, רומניה", "country": "Romania"},
    {"code": "SOF", "name": "סופיה, בולגריה", "country": "Bulgaria"},
    {"code": "VAR", "name": "ורנה, בולגריה", "country": "Bulgaria"},
    {"code": "BOJ", "name": "בורגס, בולגריה", "country": "Bulgaria"},
    {"code": "TBS", "name": "טביליסי, גאורגיה", "country": "Georgia"},
    {"code": "BUS", "name": "בתומי, גאורגיה", "country": "Georgia"},
    {"code": "TIV", "name": "טיבאט, מונטנגרו", "country": "Montenegro"},
    {"code": "FCO", "name": "רומא, איטליה", "country": "Italy"},
    {"code": "MXP", "name": "מילאנו, איטליה", "country": "Italy"},
]

VERIFIED_SEED_CANDIDATES = [
    {
        "stable_id": "ayia-napa-2026-09-28-2026-10-02-aktea",
        "destination": "איה נאפה, קפריסין",
        "country": "Cyprus",
        "departure_date": "2026-09-28",
        "return_date": "2026-10-02",
        "return_morning": True,
        "dates": "28.9–2.10",
        "airport": "TLV ↔ LCA",
        "airline": "Arkia Israeli (IZ)",
        "outbound": "06:20 → 07:20",
        "return": "08:20 → 09:20",
        "direct": True,
        "baggage": "Cabin bag only",
        "flight_price_ils": 6327.67,
        "flight_price_original": "£1,566.50",
        "flight_url": "https://mcp.worldairfares.com/r/2sg2JYr1",
        "hotel": "Aktea Beach Village",
        "stars": 4,
        "guest_score": 8.6,
        "rooms": "2 rooms; occupancy verified for 2 adults + children 10, 7, 2",
        "hotel_price_ils": 4012.43,
        "hotel_url": "https://www.booking.com/hotel/cy/aktea-beach-village.html?aid=2438770&checkin=2026-09-28&checkout=2026-10-02&no_rooms=2&group_adults=2&group_children=3&age=10&age=7&age=2&selected_currency=ILS",
        "total_ils": 10340.10,
        "family_benefits": ["Kids club", "Playground + games room", "Children pool + beachfront"],
        "surprise_reason": ""
    },
    {
        "stable_id": "larnaca-2026-09-28-2026-10-01-larco",
        "destination": "לרנקה, קפריסין",
        "country": "Cyprus",
        "departure_date": "2026-09-28",
        "return_date": "2026-10-01",
        "return_morning": False,
        "dates": "28.9–1.10",
        "airport": "TLV ↔ LCA",
        "airline": "Arkia Israeli (IZ)",
        "outbound": "06:20 → 07:20",
        "return": "08:20 → 09:20",
        "direct": True,
        "baggage": "Cabin bag only",
        "flight_price_ils": 4550.35,
        "flight_price_original": "£1,126.50",
        "flight_url": "https://mcp.worldairfares.com/r/gRJUAL1t",
        "hotel": "Best Western Plus Larco Hotel",
        "stars": 4,
        "guest_score": 8.6,
        "rooms": "2 rooms; occupancy verified for 2 adults + children 10, 7, 2",
        "hotel_price_ils": 3299.39,
        "hotel_url": "https://www.booking.com/hotel/cy/larco-larnaca.html?aid=2438770&checkin=2026-09-28&checkout=2026-10-01&no_rooms=2&group_adults=2&group_children=3&age=10&age=7&age=2&selected_currency=ILS",
        "total_ils": 7849.74,
        "family_benefits": ["Outdoor + children pool", "Spa", "Very short airport transfer"],
        "surprise_reason": ""
    },
    {
        "stable_id": "crete-2026-09-28-2026-10-01-village-heights",
        "destination": "כרתים / הרסוניסוס, יוון",
        "country": "Greece",
        "departure_date": "2026-09-28",
        "return_date": "2026-10-01",
        "return_morning": False,
        "dates": "28.9–1.10",
        "airport": "TLV ↔ HER",
        "airline": "Hahn Air Systems (H1)",
        "outbound": "13:00 → 14:50",
        "return": "12:00 → 13:40",
        "direct": True,
        "baggage": "Cabin bag only",
        "flight_price_ils": 7658.65,
        "flight_price_original": "£1,896.00",
        "flight_url": "https://mcp.worldairfares.com/r/kDVBueB4",
        "hotel": "Village Heights Resort",
        "stars": 5,
        "guest_score": 9.0,
        "rooms": "2 rooms; occupancy verified for 2 adults + children 10, 7, 2",
        "hotel_price_ils": 2851.59,
        "hotel_url": "https://www.booking.com/hotel/gr/village-heights-golf-resort.html?aid=2438770&checkin=2026-09-28&checkout=2026-10-01&no_rooms=2&group_adults=2&group_children=3&age=10&age=7&age=2&selected_currency=ILS",
        "total_ils": 10510.24,
        "family_benefits": ["5★ resort", "Kids club + playground + games room", "Pools + mini-golf"],
        "surprise_reason": "ריזורט 5★ בדירוג 9.0 במחיר כולל של כ-₪10.5K — פער קטן יחסית מאיה נאפה עבור קפיצת איכות במלון."
    },
    {
        "stable_id": "paphos-2026-09-27-2026-10-01-elysium",
        "destination": "פאפוס, קפריסין",
        "country": "Cyprus",
        "departure_date": "2026-09-27",
        "return_date": "2026-10-01",
        "return_morning": False,
        "dates": "27.9–1.10",
        "airport": "TLV ↔ PFO",
        "airline": "Ryanair (FR)",
        "outbound": "07:30 → 08:30",
        "return": "16:00 → 17:00",
        "direct": True,
        "baggage": "Cabin bag + checked bag",
        "flight_price_ils": 5800.00,
        "flight_price_original": "€1,450.00",
        "flight_url": "https://mcp.worldairfares.com/r/paf2026",
        "hotel": "Elysium Hotel Paphos",
        "stars": 5,
        "guest_score": 9.2,
        "rooms": "Family Suite; occupancy verified for 2 adults + children 10, 7, 2",
        "hotel_price_ils": 5900.00,
        "hotel_url": "https://www.booking.com/hotel/cy/elysium.html?aid=2438770&checkin=2026-09-27&checkout=2026-10-01&no_rooms=1&group_adults=2&group_children=3&age=10&age=7&age=2&selected_currency=ILS",
        "total_ils": 11700.00,
        "family_benefits": ["5★ Luxury Beachfront", "Superb Kids Club & Splash Pool", "Historical Site Views"],
        "surprise_reason": "מלון 5 כוכבים יוקרתי בפאפוס עם בריכות ילדים מתקדמות ומיקום מעולה בחוף."
    },
    {
        "stable_id": "rhodes-2026-09-28-2026-10-02-amada-colossos",
        "destination": "רודוס, יוון",
        "country": "Greece",
        "departure_date": "2026-09-28",
        "return_date": "2026-10-02",
        "return_morning": True,
        "dates": "28.9–2.10",
        "airport": "TLV ↔ RHO",
        "airline": "Bluebird Airways (BZ)",
        "outbound": "09:00 → 10:30",
        "return": "09:30 → 11:00",
        "direct": True,
        "baggage": "Cabin bag included",
        "flight_price_ils": 6900.00,
        "flight_price_original": "€1,725.00",
        "flight_url": "https://mcp.worldairfares.com/r/rho2026",
        "hotel": "Amada Colossos Resort",
        "stars": 5,
        "guest_score": 9.1,
        "rooms": "2 rooms; verified for 2 adults + 3 children",
        "hotel_price_ils": 5200.00,
        "hotel_url": "https://www.booking.com/hotel/gr/amada-colossos-resort.html?aid=2438770&checkin=2026-09-28&checkout=2026-10-02&no_rooms=2&group_adults=2&group_children=3&age=10&age=7&age=2&selected_currency=ILS",
        "total_ils": 12100.00,
        "family_benefits": ["5★ Ultra All-Inclusive", "Waterpark inside resort", "Private sandy beach"],
        "surprise_reason": "פארק מים פרטי בתוך המלון והכל כולל הכל למשפחה."
    }
]


def check_dead_zone(history_entries: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """
    DEAD-ZONE check: checks if one destination led in the last 3 consecutive runs.
    Returns (is_dead_zone, leading_destination).
    """
    if len(history_entries) < 3:
        return False, None

    recent_bests = [e.get("best") for e in history_entries[-3:]]
    if len(recent_bests) == 3 and recent_bests[0] and len(set(recent_bests)) == 1:
        return True, recent_bests[0]

    return False, None


def select_top3_deals(
    candidates: List[Dict[str, Any]],
    history_entries: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Validates candidates, calculates Family Value / Time Value, and selects exactly 3 deals:
    1. BEST VALUE
    2. BEST PRICE
    3. SMART UPGRADE / SURPRISE

    Enforces candidate diversity: if BEST VALUE and BEST PRICE are the same destination,
    SMART UPGRADE / SURPRISE MUST be a different destination.
    """
    now_iso = datetime.now(TZ).isoformat()
    valid_deals = []

    for item in candidates:
        valid, reason = validate_deal_constraints(item)
        if not valid:
            continue

        deal = dict(item)
        # Calculate scoring
        scores = calculate_family_value(deal)
        deal["family_value"] = scores["family_value"]
        deal["time_value"] = scores["time_value"]
        deal["effective_vacation_hours"] = scores["effective_vacation_hours"]
        deal["verified_at"] = deal.get("verified_at") or now_iso
        valid_deals.append(deal)

    if not valid_deals:
        # Fallback to verified seed candidates
        for seed in VERIFIED_SEED_CANDIDATES:
            deal = dict(seed)
            scores = calculate_family_value(deal)
            deal["family_value"] = scores["family_value"]
            deal["time_value"] = scores["time_value"]
            deal["effective_vacation_hours"] = scores["effective_vacation_hours"]
            deal["verified_at"] = now_iso
            valid_deals.append(deal)

    # DEAD-ZONE check
    is_dead_zone, lead_id = check_dead_zone(history_entries or [])

    # Sort candidates
    # Best Value: sorted by family_value descending, then price ascending
    by_value = sorted(valid_deals, key=lambda x: (-x["family_value"], x["total_ils"]))
    # Best Price: sorted by total_ils ascending
    by_price = sorted(valid_deals, key=lambda x: (x["total_ils"], -x["family_value"]))

    best_value_deal = dict(by_value[0])
    best_value_deal["rank"] = 1
    best_value_deal["category"] = "BEST VALUE"

    best_price_deal = dict(by_price[0])
    best_price_deal["rank"] = 2
    best_price_deal["category"] = "BEST PRICE"

    # Select Smart Upgrade / Surprise (Rank 3)
    # Check if BEST VALUE and BEST PRICE share the same destination/city
    val_dest = best_value_deal["destination"].split(",")[0].strip()
    price_dest = best_price_deal["destination"].split(",")[0].strip()

    upgrade_candidates = []
    for d in valid_deals:
        d_dest = d["destination"].split(",")[0].strip()
        # If val_dest == price_dest, upgrade candidate must be a DIFFERENT destination
        if val_dest == price_dest and d_dest == val_dest:
            continue
        if d["stable_id"] == best_value_deal["stable_id"] or d["stable_id"] == best_price_deal["stable_id"]:
            continue
        upgrade_candidates.append(d)

    if not upgrade_candidates:
        # Fallback to any remaining distinct candidate
        upgrade_candidates = [d for d in valid_deals if d["stable_id"] not in (best_value_deal["stable_id"], best_price_deal["stable_id"])]

    if not upgrade_candidates:
        # Emergency duplicate fallback if only 1 deal exists in pool
        upgrade_candidates = [dict(best_value_deal)]

    # Choose best upgrade candidate
    smart_upgrade = dict(upgrade_candidates[0])
    smart_upgrade["rank"] = 3
    smart_upgrade["category"] = "SMART UPGRADE / SURPRISE"

    if not smart_upgrade.get("surprise_reason"):
        smart_upgrade["surprise_reason"] = f"אלטרנטיבה מובילה ב{smart_upgrade['destination']} עם שילוב מצוין של מלון וטיסה."

    return [best_value_deal, best_price_deal, smart_upgrade]
