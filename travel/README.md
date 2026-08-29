# Family Travel Deal Monitor — Sukkot 2026

Public dashboard: `/travel/` on this repository's GitHub Pages site.

## What is installed

- Hourly GitHub Actions workflow (`7 * * * *` UTC schedule trigger)
- RTL public dashboard in `travel/index.html`
- Last-known-good data in `travel/data.json`
- Append-only lightweight run history in `travel/history.jsonl`
- Hard validation for the Sukkot windows:
  - depart 2026-09-27 or 2026-09-28
  - return 2026-10-01 or 2026-10-02 morning only
  - Turkey and Arab-country destinations excluded
- Exactly three ranked outputs: BEST VALUE, BEST PRICE, SMART UPGRADE / SURPRISE
- Meaningful-change detection (new deal, price drop >= ₪300 or >= 3%, BEST VALUE change)
- GitHub Issue notification on meaningful changes
- Last-known-good preservation if a provider fails or returns invalid data

## Live-provider integration

The repository runner supports an external normalized JSON feed through the repository secret `TRAVEL_PROVIDER_JSON_URL`. Until provider adapters are implemented, the dashboard preserves the last verified live snapshot instead of fabricating fresh prices.

Provider adapters should use official/authorized API access and GitHub Secrets for credentials. Never commit API keys or authentication tokens.

## Normalized provider contract

A provider response must contain exactly three deals in this order:

1. `BEST VALUE`
2. `BEST PRICE`
3. `SMART UPGRADE / SURPRISE`

Each deal must include at least:

- `stable_id`
- `category`
- `destination`
- `departure_date`
- `return_date`
- `return_morning` when returning on 2026-10-02
- `flight_url`
- `hotel_url`
- `total_ils`

The dashboard may include additional fields such as airline, times, baggage, hotel rating, Family Value, Effective Vacation Time and family benefits.

## Reliability rule

A failed, stale or unverifiable provider must never silently replace a known-good result. `monitor.py` validates the payload first and keeps the last verified snapshot when validation fails.
