"""
Playwright async client example — integrates with the Proxy Rotator API.
Replace BASE with your actual Railway app URL before using.

Install: pip install playwright httpx && playwright install chromium
"""

import asyncio
import httpx
from playwright.async_api import async_playwright

BASE = "https://your-app.up.railway.app"


async def get_proxy():
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/get-proxy")
        return r.json()["proxy"]


async def report_dead(proxy):
    async with httpx.AsyncClient() as c:
        await c.post(f"{BASE}/report-dead", params={"proxy": proxy})


async def scrape(url, max_retries=3):
    for attempt in range(max_retries):
        proxy = await get_proxy()
        async with async_playwright() as p:
            browser = await p.chromium.launch(proxy={"server": proxy})
            page = await browser.new_page()
            try:
                await page.goto(url, timeout=15000)
                content = await page.content()
                await browser.close()
                return content
            except Exception as e:
                print(f"Attempt {attempt + 1} failed via {proxy}: {e}")
                await report_dead(proxy)
                await browser.close()
    raise Exception("All retries failed")


if __name__ == "__main__":
    result = asyncio.run(scrape("https://api.ipify.org"))
    print(result[:500])
