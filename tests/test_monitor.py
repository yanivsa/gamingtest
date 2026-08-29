"""
Comprehensive Unit & Integration Tests for Sukkot 2026 Travel Monitor.
"""
import unittest
import json
import os
from copy import deepcopy

from providers import (
    WorldAirfaresAdapter,
    BookingComAdapter,
    SkyscannerAdapter,
    EDreamsAdapter,
    BreckenWanderAdapter,
    check_all_providers,
)
from travel_engine.constraints import (
    is_destination_excluded,
    is_valid_date_pair,
    is_valid_return_schedule,
    validate_deal_constraints,
)
from travel_engine.scoring import (
    score_outbound_time,
    score_return_time,
    calculate_effective_vacation_hours,
    calculate_family_value,
)
from travel_engine.selector import (
    select_top3_deals,
    VERIFIED_SEED_CANDIDATES,
    check_dead_zone,
)
from monitor import validate, meaningful


class TestConstraints(unittest.TestCase):
    def test_allowed_date_pairs(self):
        valid_pairs = [
            ("2026-09-27", "2026-10-01"),
            ("2026-09-27", "2026-10-02"),
            ("2026-09-28", "2026-10-01"),
            ("2026-09-28", "2026-10-02"),
        ]
        for dep, ret in valid_pairs:
            self.assertTrue(is_valid_date_pair(dep, ret), f"Pair {dep}->{ret} should be valid")

        invalid_pairs = [
            ("2026-09-26", "2026-10-01"),
            ("2026-09-27", "2026-10-03"),
            ("2026-09-29", "2026-10-01"),
        ]
        for dep, ret in invalid_pairs:
            self.assertFalse(is_valid_date_pair(dep, ret), f"Pair {dep}->{ret} should be invalid")

    def test_return_morning_rule_for_oct_2(self):
        # On 2026-10-02, departure < 12:00 is required
        self.assertTrue(is_valid_return_schedule("2026-10-02", "08:20 → 09:20", True))
        self.assertTrue(is_valid_return_schedule("2026-10-02", "10:30", True))
        self.assertFalse(is_valid_return_schedule("2026-10-02", "14:00 → 15:00", True))
        self.assertFalse(is_valid_return_schedule("2026-10-02", "08:20 → 09:20", False))

    def test_destination_exclusion_policy(self):
        excluded = [
            "אנטליה, טורקיה",
            "שארם א-שייח, מצרים",
            "עמאן, ירדן",
            "דובאי, איחוד האמירויות",
            "דוחה, קטר",
            "איסטנבול, טורקיה",
        ]
        for dest in excluded:
            self.assertTrue(is_destination_excluded(dest), f"Destination '{dest}' should be excluded")

        allowed = [
            "לרנקה, קפריסין",
            "איה נאפה, קפריסין",
            "הרסוניסוס, כרתים",
            "רודוס, יוון",
            "פראג, צ'כיה",
        ]
        for dest in allowed:
            self.assertFalse(is_destination_excluded(dest), f"Destination '{dest}' should be allowed")


class TestScoring(unittest.TestCase):
    def test_outbound_flight_scoring(self):
        score, desc = score_outbound_time("06:20")
        self.assertEqual(score, 100.0)

        score, desc = score_outbound_time("12:30")
        self.assertEqual(score, 80.0)

        score, desc = score_outbound_time("15:00")
        self.assertEqual(score, 60.0)

        score, desc = score_outbound_time("19:00")
        self.assertEqual(score, 30.0)

        score, desc = score_outbound_time("04:30")
        self.assertEqual(score, 60.0)

    def test_return_flight_scoring(self):
        # 2026-10-01
        score, _ = score_return_time("2026-10-01", "16:00")
        self.assertEqual(score, 100.0)

        score, _ = score_return_time("2026-10-01", "10:00")
        self.assertEqual(score, 40.0)

        # 2026-10-02
        score, _ = score_return_time("2026-10-02", "08:30")
        self.assertEqual(score, 100.0)

        score, _ = score_return_time("2026-10-02", "14:00")
        self.assertEqual(score, 0.0)

    def test_effective_vacation_hours_calculation(self):
        hours = calculate_effective_vacation_hours(
            "2026-09-28", "06:20 → 07:20",
            "2026-10-02", "08:20 → 09:20"
        )
        self.assertGreater(hours, 80)
        self.assertLess(hours, 105)


class TestDealSelector(unittest.TestCase):
    def test_top3_selection_and_diversity(self):
        results = select_top3_deals(VERIFIED_SEED_CANDIDATES)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["category"], "BEST VALUE")
        self.assertEqual(results[1]["category"], "BEST PRICE")
        self.assertEqual(results[2]["category"], "SMART UPGRADE / SURPRISE")

        # Diversity check: if rank 1 and 2 share same destination city, rank 3 must be different
        val_city = results[0]["destination"].split(",")[0].strip()
        price_city = results[1]["destination"].split(",")[0].strip()
        upgrade_city = results[2]["destination"].split(",")[0].strip()

        if val_city == price_city:
            self.assertNotEqual(upgrade_city, val_city, "Rank 3 must be a distinct destination when Rank 1 and 2 are identical")

    def test_dead_zone_detection(self):
        history = [
            {"best": "larnaca-1"},
            {"best": "larnaca-1"},
            {"best": "larnaca-1"},
        ]
        is_dz, lead = check_dead_zone(history)
        self.assertTrue(is_dz)
        self.assertEqual(lead, "larnaca-1")


class TestProviderAdapters(unittest.TestCase):
    def test_provider_health_missing_credentials(self):
        adapters = [
            WorldAirfaresAdapter(secrets={}),
            BookingComAdapter(secrets={}),
            SkyscannerAdapter(secrets={}),
            EDreamsAdapter(secrets={}),
            BreckenWanderAdapter(secrets={}),
        ]
        for a in adapters:
            h = a.check_health()
            self.assertEqual(h["status"], "missing_credentials")

    def test_provider_health_configured(self):
        secrets = {
            "WORLD_AIRFARES_API_KEY": "dummy_key",
            "BOOKING_API_KEY": "dummy_key",
            "SKYSCANNER_API_KEY": "dummy_key",
            "EDREAMS_API_KEY": "dummy_key",
            "BRECKENWANDER_API_KEY": "dummy_key",
        }
        res = check_all_providers(secrets)
        for h in res:
            self.assertEqual(h["status"], "ok")


class TestPriceDropAlerts(unittest.TestCase):
    def test_meaningful_change_price_drop(self):
        old_data = {
            "deals": [
                {"stable_id": "d1", "destination": "Larnaca", "total_ils": 10000}
            ]
        }
        new_data = {
            "deals": [
                {"stable_id": "d1", "destination": "Larnaca", "total_ils": 9500}
            ]
        }
        events = meaningful(old_data, new_data)
        self.assertTrue(any("PRICE DROP" in e for e in events))


if __name__ == "__main__":
    unittest.main()
