import random
import time
import threading


class ProxyPool:
    def __init__(self):
        self._lock = threading.Lock()   # Thread-safe for concurrent loops
        self.proxies = set()            # Use a set — no duplicates ever
        self.last_fetch_time = None
        self.last_recheck_time = None
        self.total_fetched = 0
        self.total_evicted = 0
        self.fetch_cycles = 0
        self.recheck_cycles = 0

    def add(self, proxy: str):
        with self._lock:
            self.proxies.add(proxy)

    def add_many(self, proxies: list):
        with self._lock:
            before = len(self.proxies)
            self.proxies.update(proxies)
            added = len(self.proxies) - before
            self.total_fetched += added
            return added

    def remove(self, proxy: str):
        with self._lock:
            self.proxies.discard(proxy)
            self.total_evicted += 1

    def remove_many(self, proxies: list):
        with self._lock:
            for p in proxies:
                self.proxies.discard(p)
            self.total_evicted += len(proxies)

    def get_random(self) -> str | None:
        with self._lock:
            if not self.proxies:
                return None
            return random.choice(list(self.proxies))

    def snapshot(self) -> list:
        """Safe copy of pool for re-validation loop"""
        with self._lock:
            return list(self.proxies)

    def stats(self) -> dict:
        with self._lock:
            return {
                "live_proxies": len(self.proxies),
                "total_fetched_all_time": self.total_fetched,
                "total_evicted_all_time": self.total_evicted,
                "fetch_cycles_completed": self.fetch_cycles,
                "recheck_cycles_completed": self.recheck_cycles,
                "last_fetch": self.last_fetch_time,
                "last_recheck": self.last_recheck_time,
            }


# Global singleton used by all modules
pool = ProxyPool()
