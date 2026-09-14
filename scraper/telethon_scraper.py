"""Telethon scraper — collects messages from public channels/groups,
extracts entities, and posts new findings to the Flask API."""
import os, re, json, time, hashlib, asyncio
import requests
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import Message
from phonenumbers import PhoneNumberMatcher, is_valid_number, format_number, PhoneNumberFormat, region_code_for_number
import tldextract
from dotenv import load_dotenv

load_dotenv()

API_ID   = int(os.environ["TG_API_ID"])
API_HASH = os.environ["TG_API_HASH"]
SESSION  = os.environ.get("TG_SESSION_NAME", "osint_scraper")
CHANNELS = [c.strip() for c in os.environ.get("TG_TARGET_CHANNELS", "").split(",") if c.strip()]
API_BASE = os.environ.get("API_BASE", "http://app:5000")

URL_RE   = re.compile(r"https?://[^\s<>\"')]+", re.I)
DOM_RE   = re.compile(r"\b(?:[a-z0-9-]+\.)+[a-z]{2,}\b", re.I)
TG_RE    = re.compile(r"(?:https?://)?t\.me/(?:joinchat/)?([A-Za-z0-9_+\-]+)", re.I)
GAMES    = ["slot","jdb","pgslot","pragmatic","joker","jili","jackpot","918kiss",
            "mega888","xo slot","live22","habanero","baccarat","casino","สล็อต","bet"]

client = TelegramClient(f"session/{SESSION}", API_ID, API_HASH)

def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", "ignore")).hexdigest()

def extract(text: str) -> dict:
    urls    = {u.rstrip(".,)") for u in URL_RE.findall(text)}
    domains = set()
    for d in DOM_RE.findall(text):
        ext = tldextract.extract(d)
        if ext.suffix and ext.domain:
            domains.add(ext.registered_domain)
    tg = {f"t.me/{m}" for m in TG_RE.findall(text)}
    phones = set()
    for m in PhoneNumberMatcher(text, None):
        if is_valid_number(m.number):
            phones.add((format_number(m.number, PhoneNumberFormat.E164),
                        region_code_for_number(m.number)))
    low = text.lower()
    games = {kw for kw in GAMES if kw in low}
    return {"urls": list(urls), "domains": list(domains),
            "telegram": list(tg), "phones": list(phones), "games": list(games)}

def push_to_api(payload: dict):
    """Persist extracted entities through the Flask API."""
    try:
        for d in payload["domains"]:
            requests.post(f"{API_BASE}/api/enrich/domain",
                          json={"domain": d}, timeout=20)
        # optionally report raw entity mentions
        requests.post(f"{API_BASE}/api/ingest/mentions",
                      json=payload, timeout=20)
    except Exception as e:
        print("[api] push failed:", e)

async def handle_message(msg: Message, channel: str):
    if not msg.text:
        return
    text = msg.text
    h = sha(f"{channel}:{msg.id}:{text}")
    extracted = extract(text)
    if not (extracted["domains"] or extracted["telegram"] or extracted["games"]):
        return
    payload = {
        "channel": channel,
        "message_id": msg.id,
        "date": (msg.date or datetime.utcnow()).isoformat(),
        "text": text[:5000],
        "hash": h,
        **extracted,
    }
    print(f"[+] {channel}#{msg.id} → {len(extracted['domains'])} domains, "
          f"{len(extracted['phones'])} phones, games={extracted['games']}")
    push_to_api(payload)

@client.on(events.NewMessage(chats=CHANNELS or None))
async def on_new(event):
    chat = await event.get_chat()
    uname = getattr(chat, "username", None) or str(chat.id)
    await handle_message(event.message, uname)

async def backfill(limit_per_channel=500):
    """Initial historical scrape."""
    for ch in CHANNELS:
        try:
            print(f"[*] backfilling {ch} (limit={limit_per_channel})")
            async for msg in client.iter_messages(ch, limit=limit_per_channel):
                await handle_message(msg, ch)
                await asyncio.sleep(0.15)   # gentle pace
        except Exception as e:
            print(f"[!] backfill {ch} failed: {e}")

async def main():
    await client.start()
    me = await client.get_me()
    print(f"[+] logged in as {me.username or me.id}")
    await backfill()
    print("[*] listening for live messages...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())