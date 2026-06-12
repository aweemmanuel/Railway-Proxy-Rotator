import asyncio
import time
import traceback
from fetcher import fetch_all
from validator import validate_list
from pool import pool

FETCH_INTERVAL_SECONDS   = 15 * 60   # Loop A: every 15 min
RECHECK_INTERVAL_SECONDS =  5 * 60   # Loop B: every 5 min


async def fetch_and_validate_loop():
    while True:
        try:
            cycle_start = time.time()
            print(f"\n[LOOP A] ── Fetch cycle starting ──────────────────────", flush=True)

            raw = await fetch_all()
            print(f"[LOOP A] Raw proxies fetched: {len(raw)}", flush=True)

            if raw:
                print(f"[LOOP A] Validating {len(raw)} proxies...", flush=True)
                live, dead = await validate_list(raw)
                added = pool.add_many(live)
                pool.last_fetch_time = time.time()
                pool.fetch_cycles += 1

                elapsed = round(time.time() - cycle_start, 1)
                print(f"[LOOP A] ✓ Done in {elapsed}s — "
                      f"{len(live)} live / {len(raw)} tested / "
                      f"{added} new added / pool={len(pool.proxies)}", flush=True)
            else:
                print("[LOOP A] ⚠ No proxies fetched — all sources failed or blocked", flush=True)

        except Exception as e:
            print(f"[LOOP A] ❌ ERROR: {e}", flush=True)
            traceback.print_exc()

        print(f"[LOOP A] Sleeping {FETCH_INTERVAL_SECONDS // 60} minutes...\n", flush=True)
        await asyncio.sleep(FETCH_INTERVAL_SECONDS)


async def recheck_pool_loop():
    while True:
        await asyncio.sleep(RECHECK_INTERVAL_SECONDS)

        try:
            snapshot = pool.snapshot()
            if not snapshot:
                print("[LOOP B] Pool empty — skipping recheck", flush=True)
                continue

            print(f"\n[LOOP B] ── Recheck cycle — {len(snapshot)} proxies ──", flush=True)
            cycle_start = time.time()

            live, dead = await validate_list(snapshot)

            if dead:
                pool.remove_many(dead)

            pool.last_recheck_time = time.time()
            pool.recheck_cycles += 1

            elapsed = round(time.time() - cycle_start, 1)
            print(f"[LOOP B] ✓ Done in {elapsed}s — "
                  f"{len(live)} still live / {len(dead)} evicted / "
                  f"pool={len(pool.proxies)}", flush=True)

        except Exception as e:
            print(f"[LOOP B] ❌ ERROR: {e}", flush=True)
            traceback.print_exc()

        print(f"[LOOP B] Sleeping {RECHECK_INTERVAL_SECONDS // 60} minutes...\n", flush=True)
