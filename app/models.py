from datetime import datetime
from sqlalchemy import (Column, Integer, String, DateTime, ForeignKey, Text,
                        Table, Float, UniqueConstraint, Index)
from sqlalchemy.orm import relationship
from extensions import db

# Many-to-many: Domain <-> IP
domain_ip = Table(
    "domain_ip", db.metadata,
    Column("domain_id", Integer, ForeignKey("domains.id"), primary_key=True),
    Column("ip_id", Integer, ForeignKey("ip_addresses.id"), primary_key=True),
    Column("first_seen", DateTime, default=datetime.utcnow),
    Column("last_seen", DateTime, default=datetime.utcnow),
)

# Many-to-many: Campaign <-> Domain
campaign_domain = Table(
    "campaign_domain", db.metadata,
    Column("campaign_id", Integer, ForeignKey("campaigns.id"), primary_key=True),
    Column("domain_id", Integer, ForeignKey("domains.id"), primary_key=True),
)


class Campaign(db.Model):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), index=True)          # e.g. "Lucky Slot MM"
    game_name = Column(String(255), index=True)
    country = Column(String(4), index=True)         # ISO-2
    first_seen = Column(DateTime, default=datetime.utcnow, index=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    source = Column(String(64))                     # telegram / web / manual
    notes = Column(Text)

    domains = relationship("Domain", secondary=campaign_domain,
                           back_populates="campaigns")
    phones = relationship("PhoneNumber", back_populates="campaign")


class Domain(db.Model):
    __tablename__ = "domains"
    id = Column(Integer, primary_key=True)
    fqdn = Column(String(255), unique=True, index=True)
    registrable = Column(String(255), index=True)
    tld = Column(String(32), index=True)
    registrar = Column(String(255))
    registrant_country = Column(String(4))
    creation_date = Column(DateTime)
    updated_date = Column(DateTime)
    expiry_date = Column(DateTime)
    first_seen = Column(DateTime, default=datetime.utcnow, index=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    raw_whois = Column(Text)

    ips = relationship("IPAddress", secondary=domain_ip, back_populates="domains")
    campaigns = relationship("Campaign", secondary=campaign_domain,
                             back_populates="domains")


class IPAddress(db.Model):
    __tablename__ = "ip_addresses"
    id = Column(Integer, primary_key=True)
    ip = Column(String(45), unique=True, index=True)
    asn = Column(String(32), index=True)
    asn_name = Column(String(255))
    country = Column(String(4), index=True)
    city = Column(String(128))
    isp = Column(String(255))
    org = Column(String(255))
    hostname = Column(String(255))
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

    domains = relationship("Domain", secondary=domain_ip, back_populates="ips")


class PhoneNumber(db.Model):
    __tablename__ = "phone_numbers"
    id = Column(Integer, primary_key=True)
    raw = Column(String(64))
    e164 = Column(String(32), unique=True, index=True)
    country = Column(String(4), index=True)
    carrier = Column(String(128))
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    first_seen = Column(DateTime, default=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="phones")


class TgChannel(db.Model):
    __tablename__ = "tg_channels"
    id = Column(Integer, primary_key=True)
    username = Column(String(128), unique=True, index=True)
    title = Column(String(255))
    kind = Column(String(32))  # channel / group
    first_seen = Column(DateTime, default=datetime.utcnow)


class TgMessage(db.Model):
    __tablename__ = "tg_messages"
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey("tg_channels.id"), index=True)
    message_id = Column(Integer, index=True)
    date = Column(DateTime, index=True)
    text = Column(Text)
    raw = Column(Text)
    hash = Column(String(64), unique=True, index=True)  # dedupe
    __table_args__ = (Index("ix_tg_channel_msg", "channel_id", "message_id"),)


class EntityMention(db.Model):
    __tablename__ = "entity_mentions"
    id = Column(Integer, primary_key=True)
    kind = Column(String(32), index=True)       # url/domain/phone/tg/game
    value = Column(String(512), index=True)
    source_type = Column(String(32))            # tg/web
    source_id = Column(Integer)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("kind", "value", "source_type", "source_id",
                                       name="uq_entity_src"),)