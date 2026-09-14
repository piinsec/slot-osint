"""Cluster domains by shared IP / ASN — syndicate network detection."""
from collections import defaultdict
from extensions import db
from models import Domain, IPAddress

def cluster_by_asn() -> dict:
    """Return { asn: { asn_name, domains: [...], ips: [...], countries: [...] } }"""
    rows = (db.session.query(Domain, IPAddress)
            .join(Domain.ips)
            .all())
    buckets = defaultdict(lambda: {"asn_name": None, "domains": set(),
                                    "ips": set(), "countries": set()})
    for dom, ip in rows:
        key = ip.asn or f"ip:{ip.ip}"
        b = buckets[key]
        b["asn_name"] = b["asn_name"] or ip.asn_name
        b["domains"].add(dom.fqdn)
        b["ips"].add(ip.ip)
        if ip.country:
            b["countries"].add(ip.country)

    return {
        k: {
            "asn": k,
            "asn_name": v["asn_name"],
            "domains": sorted(v["domains"]),
            "ips": sorted(v["ips"]),
            "countries": sorted(v["countries"]),
            "domain_count": len(v["domains"]),
        }
        for k, v in buckets.items()
    }

def graph_payload():
    """Build D3-ready nodes/links: campaigns ↔ domains ↔ IPs, with ASN edges."""
    nodes, links = [], []
    seen = set()

    def add_node(nid, label, kind, **extra):
        if nid in seen:
            return
        seen.add(nid)
        nodes.append({"id": nid, "label": label, "kind": kind, **extra})

    domains = Domain.query.limit(2000).all()
    for d in domains:
        add_node(f"d:{d.fqdn}", d.fqdn, "domain")
        for ip in d.ips:
            add_node(f"ip:{ip.ip}", ip.ip, "ip",
                     asn=ip.asn, country=ip.country, asn_name=ip.asn_name)
            links.append({"source": f"d:{d.fqdn}", "target": f"ip:{ip.ip}",
                          "kind": "resolves"})
        for c in d.campaigns:
            add_node(f"c:{c.id}", c.name or f"campaign-{c.id}", "campaign",
                     country=c.country, game=c.game_name)
            links.append({"source": f"c:{c.id}", "target": f"d:{d.fqdn}",
                          "kind": "promotes"})

    return {"nodes": nodes, "links": links}