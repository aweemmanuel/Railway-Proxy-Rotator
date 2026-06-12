import httpx
import asyncio

SOURCES = [
    # ── Tier 1: Most reliable, updated every 5 min ───────────────
    "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&timeout=5000&simplified=true",
    "https://api.proxyscrape.com/v4/free-proxy-list/get?request=getproxies&protocol=http",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
    "https://raw.githubusercontent.com/databay-labs/free-proxy-list/main/http.txt",

    # ── Tier 2: GitHub raw lists ──────────────────────────────────
    "https://raw.githubusercontent.com/Thordata/awesome-free-proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/generated/http_proxies.txt",
]


async def fetch_source(client: httpx.AsyncClient, url: str) -> list:
    try:
        r = await client.get(url, timeout=15)
        proxies = []
        for line in r.text.strip().split("\n"):
            line = line.strip()
            # Must look like host:port
            if ":" in line and not line.startswith("#") and not line.startswith("<"):
                host_port = line.split("//")[-1]  # strip http:// prefix if present
                parts = host_port.split(":")
                if len(parts) == 2 and parts[1].strip().isdigit():
                    proxies.append(f"http://{host_port}")
        print(f"  ✓ {len(proxies):>4} from {url[8:60]}...", flush=True)
        return proxies
    except Exception as e:
        print(f"  ✗ FAILED {url[8:55]} — {type(e).__name__}", flush=True)
        return []


async def fetch_all() -> list:
    print(f"[fetcher] Fetching from {len(SOURCES)} sources...", flush=True)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        results = await asyncio.gather(*[fetch_source(client, u) for u in SOURCES])
    raw = [p for batch in results for p in batch]
    unique = list(set(raw))
    print(f"[fetcher] Total unique proxies: {len(unique)}", flush=True)
    return unique
