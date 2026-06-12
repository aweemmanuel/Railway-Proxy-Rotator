from fastapi import FastAPI, HTTPException, Query
from contextlib import asynccontextmanager
from loops import fetch_and_validate_loop, recheck_pool_loop
from pool import pool
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start both loops as background tasks on boot
    asyncio.create_task(fetch_and_validate_loop())
    asyncio.create_task(recheck_pool_loop())
    print("✓ Both background loops started")
    yield


app = FastAPI(
    title="Proxy Rotator API v3",
    description="24/7 fetch → validate → recheck cycle",
    version="3.0",
    lifespan=lifespan
)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/get-proxy")
def get_proxy():
    """Returns one live proxy from the pool"""
    proxy = pool.get_random()
    if not proxy:
        raise HTTPException(503, "Pool is empty — loops are still warming up, try in 60 seconds")
    return {"proxy": proxy, **pool.stats()}


@app.get("/pool-status")
def pool_status():
    """Full stats on pool health and loop activity"""
    return pool.stats()


@app.post("/report-dead")
def report_dead(proxy: str = Query(...)):
    """
    Your automation tool calls this when a proxy fails mid-use.
    Removes it from the pool instantly — don't wait for Loop B.
    """
    pool.remove(proxy)
    return {"status": "removed", "proxy": proxy, **pool.stats()}


@app.post("/force-fetch")
async def force_fetch():
    """Manually trigger a full fetch + validate cycle right now"""
    from fetcher import fetch_all
    from validator import validate_list
    raw = await fetch_all()
    live, dead = await validate_list(raw)
    added = pool.add_many(live)
    return {"status": "done", "added": added, **pool.stats()}


@app.get("/health")
def health():
    return {"status": "ok", "pool_size": len(pool.proxies)}
