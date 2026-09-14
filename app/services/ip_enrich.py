"""IP enrichment via ip-api.com (free) with paid fallback (ipinfo/VT)."""
import time
import requests
from config import Config
from .dns_recon import RateLimiter

_ipapi_rl = RateLimiter(per_minute=Config.IPAPI_RATE_PER_MIN)
_CACHE = {}

def enrich_ip(ip: str) -> dict:
    if ip in _CACHE:
        return _CACHE[ip]

    # Paid path
    if Config.IPINFO_TOKEN:
        try:
            r = requests.get(f"https://ipinfo.io/{ip}/json",
                             params={"token": Config.IPINFO_TOKEN}, timeout=8)
            j = r.json()
            data = {
                "ip": ip,
                "asn": j.get("org", "").split()[0] if j.get("org") else None,
                "asn_name": j.get("org"),
                "country": j.get("country"),
                "city": j.get("city"),
                "isp": j.get("org"),
                "org": j.get("org"),
                "hostname": j.get("hostname"),
            }
            _CACHE[ip] = data
            return data
        except Exception:
            pass

    # Free path — ip-api.com (45 req/min limit)
    _ipapi_rl.wait()
    try:
        r = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,country,countryCode,city,isp,org,as,asname,reverse"},
            timeout=8,
        )
        j = r.json()
        if j.get("status") != "success":
            data = {"ip": ip, "error": j.get("message", "lookup failed")}
        else:
            data = {
                "ip": ip,
                "asn": (j.get("as") or "").split()[0] or None,
                "asn_name": j.get("asname"),
                "country": j.get("countryCode"),
                "city": j.get("city"),
                "isp": j.get("isp"),
                "org": j.get("org"),
                "hostname": j.get("reverse"),
            }
    except Exception as e:
        data = {"ip": ip, "error": str(e)}

    _CACHE[ip] = data
    return data