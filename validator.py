import httpx
import asyncio

# Multiple fallback test URLs — tries each one, proxy is live if ANY succeeds
TEST_URLS = [
    "http://ip-api.com/json",        # Very reliable, returns JSON with IP info
    "http://checkip.amazonaws.com",  # AWS, almost always up
    "http://ifconfig.me/ip",         # Simple IP echo
    "http://api.ipify.org",          # Reliable IP echo
]

TIMEOUT        = 8.0    # Increased from 5s — gives slow proxies a chance
MAX_CONCURRENT = 80     # Reduced slightly — Railway free plan safer at 80

async def check(proxy: str, semaphore: asyncio.Semaphore) -> tuple[str, bool]:
    async with semaphore:
        for url in TEST_URLS:
            try:
                async with httpx.AsyncClient(
                    proxies={"http://": proxy, "https://": proxy},
                    timeout=TIMEOUT,
                    follow_redirects=True
                ) as client:
                    r = await client.get(url)
                    if r.status_code == 200:
                        return proxy, True
            except:
                continue  # Try next URL before giving up
        return proxy, False


async def validate_list(proxies: list) -> tuple[list, list]:
    """
    Returns (live_list, dead_list)
    Validates the full list with MAX_CONCURRENT parallel workers
    """
    sem = asyncio.Semaphore(MAX_CONCURRENT)
    results = await asyncio.gather(*[check(p, sem) for p in proxies])
    live = [p for p, ok in results if ok]
    dead = [p for p, ok in results if not ok]
    return live, dead
