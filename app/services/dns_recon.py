"""DNS resolution with rate limiting."""
import time
import socket
from concurrent.futures import ThreadPoolExecutor
import dns.resolver

class RateLimiter:
    def __init__(self, per_minute: int):
        self.min_interval = 60.0 / max(per_minute, 1)
        self._last = 0.0
    def wait(self):
        now = time.monotonic()
        delta = now - self._last
        if delta < self.min_interval:
            time.sleep(self.min_interval - delta)
        self._last = time.monotonic()

_resolver = dns.resolver.Resolver()
_resolver.nameservers = ["1.1.1.1", "8.8.8.8"]
_resolver.timeout = 5
_resolver.lifetime = 8

def resolve_a(domain: str):
    """Return list of IPv4 addresses for a domain."""
    try:
        answers = _resolver.resolve(domain, "A")
        return [r.address for r in answers]
    except Exception:
        return []

def resolve_mx(domain: str):
    try:
        return [str(r.exchange).rstrip(".") for r in _resolver.resolve(domain, "MX")]
    except Exception:
        return []

def resolve_ns(domain: str):
    try:
        return [str(r.target).rstrip(".") for r in _resolver.resolve(domain, "NS")]
    except Exception:
        return []

def bulk_resolve(domains, workers=8):
    out = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for d, ips in zip(domains, ex.map(resolve_a, domains)):
            out[d] = ips
    return out