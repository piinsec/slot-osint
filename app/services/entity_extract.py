"""Regex-based entity extraction for slot/gambling ads."""
import re
import tldextract
import phonenumbers

URL_RE = re.compile(r"https?://[^\s<>\"')]+", re.I)
DOMAIN_RE = re.compile(r"\b(?:[a-z0-9-]+\.)+[a-z]{2,}\b", re.I)
TG_RE = re.compile(r"(?:https?://)?t\.me/(?:joinchat/)?([A-Za-z0-9_+\-]+)", re.I)

# Game keyword list — extend with your own
GAME_KEYWORDS = [
    "slot", "jdb", "pg slot", "pgsoft", "pragmatic", "joker", "jili",
    "jackpot", "lucky", "สล็อต", "bet", "casino", "baccarat", "918kiss",
    "mega888", "pussy888", "xo slot", "live22", "spadegaming", "habanero",
]

def extract_urls(text: str):
    return list({u.rstrip(".,)") for u in URL_RE.findall(text)})

def extract_domains(text: str):
    out = set()
    for d in DOMAIN_RE.findall(text):
        ext = tldextract.extract(d)
        if ext.suffix and ext.domain:
            out.add(ext.registered_domain)
    return list(out)

def extract_telegram(text: str):
    return list({f"t.me/{m}" for m in TG_RE.findall(text)})

def extract_phones(text: str):
    """Global phone number extraction using libphonenumber."""
    results = set()
    for match in phonenumbers.PhoneNumberMatcher(text, None):
        if phonenumbers.is_valid_number(match.number):
            e164 = phonenumbers.format_number(
                match.number, phonenumbers.PhoneNumberFormat.E164)
            region = phonenumbers.region_code_for_number(match.number)
            results.add((e164, region))
    return list(results)

def extract_games(text: str):
    low = text.lower()
    return list({kw for kw in GAME_KEYWORDS if kw in low})

def extract_all(text: str) -> dict:
    return {
        "urls": extract_urls(text),
        "domains": extract_domains(text),
        "telegram": extract_telegram(text),
        "phones": extract_phones(text),
        "games": extract_games(text),
    }