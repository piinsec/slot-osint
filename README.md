# Slot/Gambling Ad OSINT Dashboard

Telegram + Web မှ slot/gambling ကြော်ငြာများကို စုဆောင်း၊ entity extract လုပ်၊
DNS/WHOIS/IP enrich လုပ်ပြီး syndicate network ကို ဖော်ထုတ်ပေးသည့် OSINT dashboard။

## Features
- 📡 Telethon scraper (public channels/groups)
- 🔍 Entity extraction (URL, domain, phone, telegram, game keyword)
- 🌐 DNS resolution + WHOIS + IP/ASN enrichment
- 🕸️ D3 network graph (campaign ↔ domain ↔ IP)
- 📊 Campaigns table + ASN/country breakdown
- 📤 Export CSV/JSON
- 🤖 Telegram bot (/enrich /stats /cluster)

## Stack
Flask · PostgreSQL · Telethon · Nginx · D3.js · Docker Compose

## Quick Start
```bash
cp .env.example .env
# .env ကို edit ပါ
docker compose up -d --build

Dashboard: http://localhost/
Graph: http://localhost/graph

