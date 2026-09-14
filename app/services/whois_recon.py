"""WHOIS lookups with rate limiting and caching in DB."""
import time
from datetime import datetime
import whois
from .dns_recon import RateLimiter

_whois_rl = RateLimiter(per_minute=10)

def _to_dt(v):
    if isinstance(v, list):
        v = v[0] if v else None
    if isinstance(v, datetime):
        return v
    return None

def lookup_whois(domain: str) -> dict:
    _whois_rl.wait()
    try:
        w = whois.whois(domain)
    except Exception as e:
        return {"error": str(e)}

    return {
        "registrar": w.registrar,
        "registrant_country": w.country,
        "creation_date": _to_dt(w.creation_date),
        "updated_date": _to_dt(w.updated_date),
        "expiry_date": _to_dt(w.expiration_date),
        "raw": str(w),
    }