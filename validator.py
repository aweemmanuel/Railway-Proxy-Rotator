import httpx
import asyncio
import random

# Multiple lightweight test targets - plain HTTP, no HTTPS needed
TEST_URLS = [
    "http://ip-api.com/json",
    "http://checkip.amazonaws.com",
    "http://api.ipify.org",
    "http://ifconfig.me/ip",
    "http://icanhazip.com",
    "http://ipecho.net/plain",
]

TIMEOUT        = 10.0   # generous timeout
MAX_CONCURRENT = 50     # conservative — Railway free tier


async def check(proxy: str, semaphore: asyncio.Semaphore) -> tuple[str, bool]:
    async with semaphore:
        # Pick a random test URL to spread load
        url = random.choice(TEST_URLS)
        try:
            async with httpx.AsyncClient(
                proxies={"http://": proxy, "https://": proxy},
                timeout=httpx.Timeout(TIMEOUT),
                follow_redirects=True,
                verify=False,  # Don't fail on SSL issues
            ) as client:
                r = await client.get(url)
                # Accept any 2xx response — we just need the proxy to route
                if 200 <= r.status_code < 300 and len(r.text.strip()) > 0:
                    return proxy, True
        except Exception:
            pass
        return proxy, False


async def validate_list(proxies: list) -> tuple[list, list]:
    """
    Returns (live_list, dead_list).
    Splits into batches of 200 to avoid overwhelming Railway's network.
    """
    if not proxies:
        return [], []

    sem = asyncio.Semaphore(MAX_CONCURRENT)
    live = []
    dead = []

    # Process in batches of 200
    batch_size = 200
    total = len(proxies)
    for i in range(0, total, batch_size):
        batch = proxies[i:i + batch_size]
        print(f"  [validator] Batch {i // batch_size + 1}/{(total + batch_size - 1) // batch_size} "
              f"— checking {len(batch)} proxies...", flush=True)
        results = await asyncio.gather(*[check(p, sem) for p in batch])
        batch_live = [p for p, ok in results if ok]
        batch_dead = [p for p, ok in results if not ok]
        live.extend(batch_live)
        dead.extend(batch_dead)
        print(f"  [validator] Batch done — {len(batch_live)} live / {len(batch_dead)} dead", flush=True)
        # Small pause between batches
        await asyncio.sleep(1)

    return live, dead
