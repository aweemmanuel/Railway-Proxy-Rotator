import asyncio
import time
from fetcher import fetch_all
from validator import validate_list
from pool import pool

FETCH_INTERVAL_SECONDS   = 15 * 60   # Loop A: fetch + validate new proxies every 15 min
RECHECK_INTERVAL_SECONDS =  5 * 60   # Loop B: re-check live pool every 5 min


# ── LOOP A: Continuously fetch new proxies and validate them ─────────────────
async def fetch_and_validate_loop():
    """
    Runs 24/7. Every 15 minutes:
      1. Pulls fresh raw proxies from all sources
      2. Validates every one concurrently
      3. Adds only live proxies to the pool
      4. Never adds duplicates (pool is a set)
    """
    while True:
        try:
            cycle_start = time.time()
            print(f"\n[LOOP A] ── Fetch cycle starting ──────────────────────")

            raw = await fetch_all()

            if raw:
                print(f"[LOOP A] Validating {len(raw)} proxies...")
                live, dead = await validate_list(raw)
                added = pool.add_many(live)
                pool.last_fetch_time = time.time()
                pool.fetch_cycles += 1

                elapsed = round(time.time() - cycle_start, 1)
                print(f"[LOOP A] ✓ Done in {elapsed}s — "
                      f"{len(live)} live / {len(raw)} tested / "
                      f"{added} new added / pool={len(pool.proxies)}")
            else:
                print("[LOOP A] No proxies fetched — all sources failed")

        except Exception as e:
            print(f"[LOOP A] ERROR: {e}")

        print(f"[LOOP A] Sleeping {FETCH_INTERVAL_SECONDS // 60} minutes...\n")
        await asyncio.sleep(FETCH_INTERVAL_SECONDS)


# ── LOOP B: Re-check existing pool every 5 minutes ──────────────────────────
async def recheck_pool_loop():
    """
    Runs 24/7. Every 5 minutes:
      1. Takes a snapshot of all proxies currently in the pool
      2. Re-validates every single one
      3. Immediately evicts any that are now dead
      4. Logs how many were removed
    """
    while True:
        await asyncio.sleep(RECHECK_INTERVAL_SECONDS)  # wait first, pool needs time to populate

        try:
            snapshot = pool.snapshot()
            if not snapshot:
                print("[LOOP B] Pool empty — skipping recheck")
                continue

            print(f"\n[LOOP B] ── Recheck cycle starting — {len(snapshot)} proxies ──")
            cycle_start = time.time()

            live, dead = await validate_list(snapshot)

            if dead:
                pool.remove_many(dead)

            pool.last_recheck_time = time.time()
            pool.recheck_cycles += 1

            elapsed = round(time.time() - cycle_start, 1)
            print(f"[LOOP B] ✓ Done in {elapsed}s — "
                  f"{len(live)} still live / {len(dead)} evicted / "
                  f"pool={len(pool.proxies)}")

        except Exception as e:
            print(f"[LOOP B] ERROR: {e}")

        print(f"[LOOP B] Sleeping {RECHECK_INTERVAL_SECONDS // 60} minutes...\n")
