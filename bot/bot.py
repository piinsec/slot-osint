import os, logging, requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ["TG_BOT_TOKEN"]
API   = os.environ.get("API_BASE", "http://app:5000")
ALERT = os.environ.get("TG_ALERT_CHAT_ID")

async def cmd_enrich(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("usage: /enrich domain.com")
        return
    d = ctx.args[0].strip().lower()
    await update.message.reply_text(f"⏳ enriching {d}...")
    try:
        r = requests.post(f"{API}/api/enrich/domain", json={"domain": d}, timeout=30)
        j = r.json()
        await update.message.reply_text(
            f"✅ {d}\nRegistrar: {j.get('whois',{}).get('registrar')}\n"
            f"IPs: {', '.join(j.get('ips',[]))}")
    except Exception as e:
        await update.message.reply_text(f"❌ {e}")

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    r = requests.get(f"{API}/api/stats/asn", timeout=15).json()
    top = "\n".join(f"{x['asn']} · {x['name']} · {x['count']}" for x in r[:10])
    await update.message.reply_text(f"Top ASNs:\n{top}")

async def cmd_cluster(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    r = requests.get(f"{API}/api/clusters/asn", timeout=20).json()
    items = sorted(r.values(), key=lambda x: -x["domain_count"])[:5]
    out = "\n\n".join(f"ASN {c['asn']} ({c['asn_name']}) — {c['domain_count']} domains\n"
                      + ", ".join(c["domains"][:8]) for c in items)
    await update.message.reply_text(out or "No clusters yet.")

def main():
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("enrich", cmd_enrich))
    app.add_handler(CommandHandler("stats",  cmd_stats))
    app.add_handler(CommandHandler("cluster", cmd_cluster))
    print("[bot] running")
    app.run_polling()

if __name__ == "__main__":
    main()