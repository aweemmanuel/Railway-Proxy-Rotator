# 🔄 Railway Proxy Rotator v3

A 24/7 self-maintaining proxy pool with two continuous background loops.

## How It Works

Two independent loops run simultaneously:

- **Loop A** — Every 15 min: fetches fresh proxies from 10 sources, validates each one, adds live ones to the pool
- **Loop B** — Every 5 min: re-checks every proxy already in the pool, evicts any that went dead

The pool is always fresh, always live, never stale.

## Project Structure

```
proxy-rotator/
├── main.py               ← FastAPI app + all endpoints
├── fetcher.py            ← Pulls raw proxies from all sources
├── validator.py          ← Concurrent validation logic
├── pool.py               ← Thread-safe live proxy pool
├── loops.py              ← The two background loops
├── requirements.txt
├── Procfile
├── railway.json
├── example_selenium.py   ← Selenium integration example
└── example_playwright.py ← Playwright integration example
```

## Deploy to Railway

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "initial commit"
gh repo create proxy-rotator --public --push
```

### 2. Deploy on Railway

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
2. Select your repo
3. Railway auto-detects `Procfile` and deploys
4. Copy your public URL (e.g. `https://your-app.up.railway.app`)

### 3. Test It

```bash
# Check health
curl https://your-app.up.railway.app/health

# Get a proxy (may return 503 for ~60s while pool warms up)
curl https://your-app.up.railway.app/get-proxy

# Pool stats
curl https://your-app.up.railway.app/pool-status

# Force immediate fetch cycle
curl -X POST https://your-app.up.railway.app/force-fetch

# Report a dead proxy
curl -X POST "https://your-app.up.railway.app/report-dead?proxy=http://1.2.3.4:8080"
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/get-proxy` | Returns one live proxy from the pool |
| `GET` | `/pool-status` | Full stats: pool size, cycles, last fetch/recheck times |
| `POST` | `/report-dead?proxy=...` | Instantly evicts a proxy that failed in your scraper |
| `POST` | `/force-fetch` | Triggers an immediate full fetch + validate cycle |
| `GET` | `/health` | Health check (for Railway uptime monitoring) |

## Startup Timeline

```
T+0s    → Railway boots the app
T+5s    → Both loops start
T+5s    → Loop A fetches from all 10 sources immediately
T+60s   → First batch validated, pool starts populating
T+5min  → Loop B runs first recheck — evicts any already dead
T+15min → Loop A fetches again — adds new proxies from updated sources
T+20min → Loop B rechecks again
...     → Continues 24/7 forever
```

## Using the Client Examples

Edit `BASE` in `example_selenium.py` or `example_playwright.py` to point at your Railway URL, then run:

```bash
# Playwright
pip install playwright httpx
playwright install chromium
python example_playwright.py

# Selenium
pip install selenium requests
python example_selenium.py
```
