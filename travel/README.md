# Family Travel Deal Monitor — Sukkot 2026

Public dashboard: `/travel/` on this repository's GitHub Pages site.

## Overview

Autonomous family-travel deal monitor for Sukkot 2026 (2 adults + 3 children, ages 10, 7, 2).
Executes hourly via GitHub Actions runner to monitor flights, hotels, and packages within strict Sukkot date windows and family travel constraints.

## Hard Constraints

- **Family**: 2 adults + 3 children (ages 10, 7, 2).
- **Hard Sukkot Date Windows**:
  - `2026-09-27` → `2026-10-01`
  - `2026-09-27` → `2026-10-02` (morning return only)
  - `2026-09-28` → `2026-10-01`
  - `2026-09-28` → `2026-10-02` (morning return only)
- **Exclusion Policy**: Turkey and Arab country destinations are strictly excluded.
- **Departure Priority**: TLV (Ben Gurion Airport) has priority; HFA/ETM only for a real advantage.

## Provider Adapter Architecture

Provider adapters are implemented in the `providers/` package behind `BaseProviderAdapter`:

1. **World Airfares** (`WorldAirfaresAdapter` in `providers/world_airfares.py`): Primary live flight search and verification.
2. **Booking.com** (`BookingComAdapter` in `providers/booking.py`): Primary hotel verification (4-5★ hotels/resorts for 5 passengers).
3. **Skyscanner** (`SkyscannerAdapter` in `providers/skyscanner.py`): Flight discovery and cross-check.
4. **eDreams** (`EDreamsAdapter` in `providers/edreams.py`): Package and flight discovery.
5. **BreckenWander** (`BreckenWanderAdapter` in `providers/breckenwander.py`): Resort and package discovery.

### Health Statuses
Each adapter reports its health metadata in `travel/data.json` under `automation.providers`:
- `ok`: Credentials present and operational.
- `missing_credentials`: Required secret is missing from environment.
- `degraded` / `error`: API endpoint returned an error or timeout.

## Supported GitHub Actions Secrets

To enable live programmatic checks in GitHub Actions, configure the following secrets in repository settings:

- `WORLD_AIRFARES_API_KEY`: API key for World Airfares flight verification.
- `WORLD_AIRFARES_URL`: *(Optional)* Custom URL endpoint for World Airfares.
- `BOOKING_API_KEY`: API key for Booking.com hotel verification.
- `BOOKING_AFFILIATE_ID`: *(Optional)* Booking.com affiliate ID.
- `SKYSCANNER_API_KEY`: API key for Skyscanner flight discovery.
- `EDREAMS_API_KEY`: API key for eDreams package discovery.
- `BRECKENWANDER_API_KEY`: API key for BreckenWander resort discovery.
- `TRAVEL_PROVIDER_JSON_URL`: *(Optional)* External normalized JSON feed endpoint.

## Normalized Provider Output Contract

The monitor publishes exactly three deals in `travel/data.json`:

1. `BEST VALUE`
2. `BEST PRICE`
3. `SMART UPGRADE / SURPRISE`

Each deal contains:
- `rank`, `category`, `stable_id`, `destination`, `country`, `departure_date`, `return_date`, `return_morning`
- `airport`, `airline`, `outbound`, `return`, `direct`, `baggage`
- `flight_price_ils`, `flight_url`
- `hotel`, `stars`, `guest_score`, `rooms`, `hotel_price_ils`, `hotel_url`
- `total_ils`, `family_value`, `time_value`, `effective_vacation_hours`
- `family_benefits`, `surprise_reason`, `verified_at`

### Diversity Rule
If `BEST VALUE` and `BEST PRICE` share the same destination, `SMART UPGRADE / SURPRISE` MUST be a different destination whenever a verified candidate exists within budget range.

## Reliability & Fallback Rule

If external APIs fail or secrets are not configured, `monitor.py` preserves verified baseline deals and reports degraded/standby provider health status without replacing verified results with fabricated data.
