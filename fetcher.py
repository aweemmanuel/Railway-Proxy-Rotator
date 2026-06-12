import httpx
import asyncio

SOURCES = [
    # ── Tier 1: Updated every 5 minutes ──────────────────────────
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks5/data.txt",
    "https://raw.githubusercontent.com/databay-labs/free-proxy-list/main/http.txt",
    "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&timeout=5000&simplified=true",

    # ── Tier 2: Updated every 15–60 minutes ──────────────────────
    "https://raw.githubusercontent.com/Thordata/awesome-free-proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/Ian-Lusule/Proxies/main/http.txt",
    "https://raw.githubusercontent.com/iplocate/free-proxy-list/main/http.txt",
    "https://cdn.jsdelivr.net/gh/Mohammedcha/ProxRipper@main/proxies/http.txt",

    # ── Tier 3: Web APIs, no auth required ───────────────────────
    "https://api.proxyscrape.com/v4/free-proxy-list/get?request=getproxies&protocol=http",
    "https://proxyroller.com/api/get?type=http&format=text",
]


async def fetch_source(client: httpx.AsyncClient, url: str) -> list:
    try:
        r = await client.get(url, timeout=10)
        proxies = []
        for line in r.text.strip().split("\n"):
            line = line.strip()
            if ":" in line and not line.startswith("#"):
                proxies.append(
                    f"http://{line}" if not line.startswith("http") else line
                )
        print(f"  ✓ Fetched {len(proxies):>4} from {url[:55]}...")
        return proxies
    except Exception as e:
        print(f"  ✗ Source failed: {url[:55]} — {e}")
        return []


async def fetch_all() -> list:
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[fetch_source(client, u) for u in SOURCES])
    raw = [p for batch in results for p in batch]
    unique = list(set(raw))
    print(f"  → {len(unique)} unique proxies harvested from {len(SOURCES)} sources")
    return unique
