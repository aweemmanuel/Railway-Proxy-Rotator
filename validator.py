import httpx
import asyncio

TEST_URL = "http://httpbin.org/ip"   # IP-echo endpoint, confirms proxy is routing
TIMEOUT  = 5.0                        # 5 second max per proxy
MAX_CONCURRENT = 120                  # Concurrent checks (safe for Railway free plan)


async def check(proxy: str, semaphore: asyncio.Semaphore) -> tuple[str, bool]:
    async with semaphore:
        try:
            async with httpx.AsyncClient(
                proxies={"http://": proxy, "https://": proxy},
                timeout=TIMEOUT
            ) as client:
                r = await client.get(TEST_URL)
                return proxy, r.status_code == 200
        except:
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
