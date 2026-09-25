# financia.le — private free-Render edition, expanded market data

## Replace your GitHub files
Replace `app.py`, `index.html`, `render.yaml`, and `README.md` in your existing repo; leave `.gitignore` as it is. Render should redeploy automatically. Ensure your service is **Free** and has no disk or paid database.

## Render → your service → Environment
- `FINANCIA_USER`: your chosen username
- `FINANCIA_PASSWORD`: your unique strong password
- `FRED_API_KEY`: your existing FRED key (https://fred.stlouisfed.org/docs/api/api_key.html)
- `STOOQ_API_KEY`: **optional**; only if you obtain historical CSV download access from Stooq (https://stooq.com/q/d/?s=spy.us&get_apikey). Stooq can require an on-site CAPTCHA and enforce quotas. Do not place the key in HTML or GitHub.

Save and deploy. Open the Render URL and log in. The server starts refreshing data in the background; click **REFRESH MARKET DATA** if needed. Check Render logs for per-series failures. Refreshing ~60 Stooq symbols can take time and some tickers may be unsupported or blocked. Data availability is conditional, not guaranteed.

## What is in the game
- FRED: US indices where history is available, rates, macro, FX, oil, national OECD monthly indexes, etc.
- Optional Stooq: a fixed *illustrative* 50-company list (not a verified top-50-by-cap ranking); daily Close returns; named international/bond/metals ETFs. Stooq Close is **not guaranteed dividend-adjusted**. ETF returns are not the proprietary index's official return or metal spot price.
- Kraken: BTC/USD and ETH/USD recent UTC daily OHLC closes, no key required; incomplete/current UTC candle excluded. Public OHLC is limited to recent history, so crypto Q5 is unavailable without a separate deep-history source.
- Question eligibility is checked against actual available history. If a series is unavailable, the generator will not fabricate it.
- Q2–Q5 market returns end at the latest completed observation, starting 1 month/6 months/1 year/5 years earlier; Q1 is the previous session's return. Mobile has a minus/plus sign button.

## Important free-hosting limitation
Render Free erases SQLite on spin-down/restart/redeploy. Every cold start re-fetches the data and may generate a new game. A paid persistent disk or durable external storage is required to guarantee permanently frozen games. Initial game generation may be unavailable until enough data has loaded. The `/api/status` endpoint shows loaded-series counts (requires your username/password).

## Local tests
```
FINANCIA_USER=test FINANCIA_PASSWORD=test python3 app.py test
FINANCIA_USER=test FINANCIA_PASSWORD=test FRED_API_KEY=YOUR_KEY python3 app.py
```
Use your own real secret, not the example placeholder. The synthetic test does not verify external providers from your Render instance.
