from datetime import datetime
from flask import Blueprint, jsonify, request, Response
from sqlalchemy import func
from extensions import db
from models import (Campaign, Domain, IPAddress, PhoneNumber,
                    TgMessage, TgChannel, EntityMention)
from services.cluster import cluster_by_asn, graph_payload
from services.dns_recon import resolve_a
from services.whois_recon import lookup_whois
from services.ip_enrich import enrich_ip

api_bp = Blueprint("api", __name__)

# ---------- Table view ----------
@api_bp.get("/campaigns")
def list_campaigns():
    q = Campaign.query
    country = request.args.get("country")
    game = request.args.get("game")
    start = request.args.get("from")
    end = request.args.get("to")
    if country:
        q = q.filter(Campaign.country == country.upper())
    if game:
        q = q.filter(Campaign.game_name.ilike(f"%{game}%"))
    if start:
        q = q.filter(Campaign.first_seen >= datetime.fromisoformat(start))
    if end:
        q = q.filter(Campaign.first_seen <= datetime.fromisoformat(end))

    rows = q.order_by(Campaign.first_seen.desc()).limit(500).all()
    return jsonify([{
        "id": c.id, "name": c.name, "game": c.game_name,
        "country": c.country, "first_seen": c.first_seen.isoformat(),
        "domains": [d.fqdn for d in c.domains],
    } for c in rows])

@api_bp.get("/domains")
def list_domains():
    rows = Domain.query.limit(1000).all()
    return jsonify([{
        "id": d.id, "fqdn": d.fqdn, "tld": d.tld,
        "registrar": d.registrar, "country": d.registrant_country,
        "first_seen": d.first_seen.isoformat() if d.first_seen else None,
        "ips": [{"ip": i.ip, "asn": i.asn, "country": i.country} for i in d.ips],
    } for d in rows])

@api_bp.get("/stats/asn")
def stats_asn():
    rows = (db.session.query(IPAddress.asn, IPAddress.asn_name,
                             func.count(func.distinct(IPAddress.ip)))
            .group_by(IPAddress.asn, IPAddress.asn_name)
            .order_by(func.count().desc()).limit(50).all())
    return jsonify([{"asn": a, "name": n, "count": c} for a, n, c in rows])

@api_bp.get("/stats/country")
def stats_country():
    rows = (db.session.query(IPAddress.country, func.count(IPAddress.id))
            .group_by(IPAddress.country).all())
    return jsonify([{"country": c or "??", "count": n} for c, n in rows])

@api_bp.get("/graph")
def graph():
    return jsonify(graph_payload())

@api_bp.get("/clusters/asn")
def clusters_asn():
    return jsonify(cluster_by_asn())

# ---------- Enrichment endpoints ----------
@api_bp.post("/enrich/domain")
def enrich_domain():
    body = request.get_json(force=True) or {}
    fqdn = (body.get("domain") or "").strip().lower()
    if not fqdn:
        return jsonify({"error": "domain required"}), 400

    dom = Domain.query.filter_by(fqdn=fqdn).first()
    if not dom:
        import tldextract
        ext = tldextract.extract(fqdn)
        dom = Domain(fqdn=fqdn, registrable=ext.registered_domain, tld=ext.suffix)
        db.session.add(dom); db.session.flush()

    w = lookup_whois(fqdn)
    dom.registrar = w.get("registrar")
    dom.registrant_country = w.get("registrant_country")
    dom.creation_date = w.get("creation_date")
    dom.updated_date = w.get("updated_date")
    dom.expiry_date = w.get("expiry_date")
    dom.raw_whois = w.get("raw")

    for ip_str in resolve_a(fqdn):
        ip = IPAddress.query.filter_by(ip=ip_str).first()
        if not ip:
            info = enrich_ip(ip_str)
            ip = IPAddress(ip=ip_str, asn=info.get("asn"),
                           asn_name=info.get("asn_name"),
                           country=info.get("country"),
                           city=info.get("city"),
                           isp=info.get("isp"), org=info.get("org"),
                           hostname=info.get("hostname"))
            db.session.add(ip)
        if ip not in dom.ips:
            dom.ips.append(ip)

    db.session.commit()
    return jsonify({"ok": True, "domain": fqdn, "whois": {k: str(v) for k, v in w.items() if k != "raw"},
                    "ips": [i.ip for i in dom.ips]})

@api_bp.post("/enrich/ip")
def enrich_ip_api():
    body = request.get_json(force=True) or {}
    ip_str = body.get("ip")
    if not ip_str:
        return jsonify({"error": "ip required"}), 400
    return jsonify(enrich_ip(ip_str))

# ---------- Export ----------
@api_bp.get("/export/campaigns.csv")
def export_csv():
    import csv, io
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "name", "game", "country", "first_seen", "domains"])
    for c in Campaign.query.all():
        w.writerow([c.id, c.name, c.game_name, c.country,
                    c.first_seen, "|".join(d.fqdn for d in c.domains)])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=campaigns.csv"})

@api_bp.get("/export/graph.json")
def export_graph():
    return Response(__import__("json").dumps(graph_payload(), indent=2),
                    mimetype="application/json",
                    headers={"Content-Disposition": "attachment;filename=graph.json"})