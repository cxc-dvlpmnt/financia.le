# financia.le — free Render deployment

This is the free version of the private FRED-backed daily finance trivia game. It uses Python's standard library and no paid Render disk or database.

## Deploy in a few minutes

1. Create a private GitHub repository and upload `app.py`, `index.html`, `render.yaml`, `.gitignore`, and this `README.md` at its root. If replacing an older financia.le deployment, replace its `render.yaml` with this one and remove any paid persistent disk configuration; verify the Render service's instance plan is **Free** before confirming changes. A paid persistent disk may require deleting/recreating the service to move to Free.
2. Go to https://dashboard.render.com/ and choose **New > Blueprint**. Connect your repository. Confirm the service plan reads **Free**, with **no disk** and **no Postgres**. Do not confirm a paid plan.
3. Set `FINANCIA_USER` to your preferred login, `FINANCIA_PASSWORD` to a long unique password, and `FRED_API_KEY` to the free API key from https://fred.stlouisfed.org/docs/api/api_key.html. All three are backend environment variables; never paste them into `index.html` or GitHub. If Render does not prompt for them, set them under the service's **Environment** tab and redeploy.
4. Open the HTTPS `onrender.com` URL, enter your private username and password. **TRY DEMO** works immediately; real-data mode becomes available as the server fetches FRED observations. The home screen shows how many series are loaded. Use **REFRESH FRED DATA** if necessary, then try **PLAY TODAY'S GAME**.

## Important free-plan limitations

Render's free service spins down after about 15 minutes without traffic and can take about a minute to wake. Its filesystem is ephemeral: **the SQLite database, previous frozen games, and fetched observations disappear when the service sleeps, restarts, or redeploys**. The application refetches FRED data in the background at each start, and freezes the day's game again when first requested. A regenerated game **may differ** from a previous session, and historical daily-game permanence is not guaranteed. This is the trade-off for zero recurring hosting fees; do not treat it as persistent production storage.

The free service also has monthly compute, bandwidth, and build limits. Render may bill usage overages if your account has a payment method; check Render's usage and billing settings if you need a strict $0 cap. Free Render Postgres is not used because its free databases expire after 30 days.

## Data and scope

The app uses FRED for U.S. rates, inflation, GDP, FX, oil and selected U.S. equity indexes, plus OECD national share-price indexes for Japan, Germany and Korea. These are not MSCI EAFE, Emerging Markets, World, ACWI, or ACWI ex USA. This is a real-data subset, not the entire originally envisioned data universe. No fabricated values are presented in real mode; demo data is labeled simulated. FRED series history varies, and candidates without enough history are automatically ineligible.

## Test locally

With Python 3.10+:

```bash
export FINANCIA_USER='private-user'
export FINANCIA_PASSWORD='a-long-unique-password'
export FRED_API_KEY='your-fred-api-key'
python3 app.py test
python3 app.py
```

Open http://127.0.0.1:8765. Do not publish the built-in Python HTTP server directly without HTTPS; Render supplies HTTPS at its public URL.
