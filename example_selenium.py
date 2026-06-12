"""
Selenium client example — integrates with the Proxy Rotator API.
Replace BASE with your actual Railway app URL before using.
"""

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

BASE = "https://your-app.up.railway.app"


def get_proxy():
    return requests.get(f"{BASE}/get-proxy").json()["proxy"]


def report_dead(proxy):
    requests.post(f"{BASE}/report-dead", params={"proxy": proxy})


def scrape(url, retries=3):
    for attempt in range(retries):
        proxy = get_proxy()
        opts = Options()
        opts.add_argument(f"--proxy-server={proxy}")
        opts.add_argument("--headless")
        driver = webdriver.Chrome(options=opts)
        try:
            driver.get(url)
            result = driver.page_source
            driver.quit()
            return result
        except Exception as e:
            print(f"Attempt {attempt + 1} failed via {proxy}: {e}")
            report_dead(proxy)
            driver.quit()
    raise Exception("All retries exhausted")


if __name__ == "__main__":
    html = scrape("https://api.ipify.org")
    print(html[:500])
