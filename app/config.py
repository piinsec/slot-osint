import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///osint.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False

    IPAPI_RATE_PER_MIN = int(os.getenv("IPAPI_RATE_PER_MIN", 40))
    WHOIS_RATE_PER_MIN = int(os.getenv("WHOIS_RATE_PER_MIN", 10))
    DNS_WORKERS = int(os.getenv("DNS_WORKERS", 8))

    IPINFO_TOKEN = os.getenv("IPINFO_TOKEN")
    VT_API_KEY = os.getenv("VT_API_KEY")

    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")