# financia.le — private web-server edition

Five-question finance guessing game. Python standard library; no pip packages, no Node build, no MSCI CSV uploads. The app includes explicitly simulated DEMO and FRED-backed REAL modes.

## Deploy to Render (one-person recommended configuration)

1. Create a **private GitHub repository** and upload `app.py`, `index.html`, `README.md`, `.gitignore`, and `render.yaml` from this folder. Do not upload API keys or `financia.db`.
2. On [Render](https://dashboard.render.com/) choose **New → Blueprint** and connect that repository. Alternatively create a Python Web Service manually with start command `python3 app.py`, health path `/health`, and a paid instance.
3. Set these environment variables in Render **Environment** (secrets):
   - `FRED_API_KEY`: your FRED API key (see below)
   - `FINANCIA_USER`: a private login username
   - `FINANCIA_PASSWORD`: a long unique password
   - `FINANCIA_DB`: `/var/data/financia.db` (already set by render.yaml)
4. Attach a **persistent disk** mounted at `/var/data` (the Blueprint config includes a 1 GB disk). A paid service is required for Render persistent disks. Use one instance; the SQLite database is not intended to be shared between replicas.
5. Deploy, then visit your assigned HTTPS `onrender.com` URL. Your browser will ask for the private username/password. The `/health` endpoint is intentionally public for the hosting platform's health checks.
6. The server starts a FRED refresh in the background, which can take several minutes. Once observations are loaded, click **PLAY TODAY'S GAME**. The home page has **REFRESH FRED DATA** to request another background refresh. The running server also refreshes approximately every 24 hours.

### Get a FRED API key

Go to https://fred.stlouisfed.org/docs/api/api_key.html, sign in or register for a free FRED account, request an API key for this personal app, then copy the key. Put it **only** in Render → your service → Environment → `FRED_API_KEY`. Do not paste it into `index.html`, GitHub, a URL shared with others, or a client-side script. FRED API v1 is used server-side with the key in the request to `fred/series/observations`.

### Foreign-market data

No MSCI import is needed. This edition includes **OECD Financial Market: Share Prices** indexes via FRED: Japan `SPASTT01JPM661N`, Germany `SPASTT01DEM661N`, and Korea `SPASTT01KRM661N`. These are monthly national share-price indexes, 2015=100, not seasonally adjusted, and **not MSCI**, not USD-denominated MSCI indexes, and not directly interchangeable with EAFE/EM/ACWI. Their series-specific source is displayed on question reveal. The OECD/FRED series notes include attribution/copyright terms; review them if you ever open the site to others.

### Important data limitations

This is a deployable, real-data **FRED-backed subset**, not the entire original envisioned catalog. Proprietary MSCI indexes, top-50 adjusted individual stocks, Bitcoin/Ethereum, gold/silver, DXY and proprietary bond benchmarks are not connected. Do not infer that an absent feed has been replaced with simulated values: DEMO is always labeled. FRED's S&P 500/Nasdaq/Dow history may be limited, so their Q5 questions are automatically ineligible when the needed history is missing. Published real games are frozen in SQLite. If you do not attach persistent storage, redeployments may lose that history.

### Security and operations

- Use HTTPS through your host's proxy. HTTP Basic authentication protects the page and all application API routes; do not expose this directly over plaintext HTTP on the internet.
- The key and password are read from server environment variables and never sent to the browser. `/health` reveals only `{ "ok": true }`.
- A login prompt may appear once per browser session. To change the password, edit `FINANCIA_PASSWORD` in the host and redeploy.
- Browser refresh restarts in-progress play; no user answers are stored server-side.
- To back up, copy the persistent SQLite database while the service is stopped or use SQLite's backup facility. Render disk snapshots are not a substitute for independent backups.
- The daily game date rolls at 6 AM America/New_York. First real request for that game date freezes it; the data refresh may still be in progress on initial deploy, so wait for data to load.

## Run on your own server

Python 3.10+ is recommended. From the project directory:

```bash
export FINANCIA_USER='your-private-username'
export FINANCIA_PASSWORD='a-long-random-password'
export FRED_API_KEY='your-fred-api-key'
export FINANCIA_DB='/path/to/persistent/financia.db'
export PORT=8765
python3 app.py
```

Place behind a reverse proxy providing HTTPS. Do not expose the built-in Python HTTP server publicly without a TLS-terminating proxy. For a first-time manual refresh, run `python3 app.py refresh` with the same environment variables. The application starts an automatic background refresh at startup and then roughly daily.

## Files

- `app.py`: server, auth, FRED retrieval, frozen game generator and API
- `index.html`: complete responsive UI
- `render.yaml`: Render deployment Blueprint, including persistent disk
- `.gitignore`: prevents accidentally committing credentials and database files

## Check the deployment

Run `FINANCIA_USER=test FINANCIA_PASSWORD=test python3 app.py test` in a disposable environment. For local HTTP smoke testing, run the app and verify `/health` returns 200, `/` returns 401 without credentials, and `/` returns 200 with credentials.
