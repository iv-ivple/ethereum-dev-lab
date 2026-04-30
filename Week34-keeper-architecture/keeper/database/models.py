from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Enum as SAEnum
from sqlalchemy.orm import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class OpportunityStatus(str, enum.Enum):
    DETECTED   = "detected"
    EXECUTING  = "executing"
    SUCCESS    = "success"
    REVERTED   = "reverted"
    TIMEOUT    = "timeout"
    SKIPPED    = "skipped"   # below min profit

class Opportunity(Base):
    __tablename__ = "opportunities"
    id              = Column(Integer, primary_key=True)
    detected_at     = Column(DateTime, default=datetime.utcnow)
    strategy        = Column(String(64))          # e.g. "arb_triangle"
    description     = Column(Text)                # e.g. "WETH→USDC→DAI→WETH"
    gross_profit_eth = Column(Float)
    gas_cost_eth    = Column(Float)
    net_profit_eth  = Column(Float)
    input_amount_eth = Column(Float)
    status          = Column(SAEnum(OpportunityStatus), default=OpportunityStatus.DETECTED)
    tx_hash         = Column(String(66), nullable=True)
    block_number    = Column(Integer, nullable=True)
    gas_used        = Column(Integer, nullable=True)
    error_message   = Column(Text, nullable=True)
    confirmed_at    = Column(DateTime, nullable=True)

class KeeperRun(Base):
    """One row per keeper session (start → stop)."""
    __tablename__ = "keeper_runs"
    id              = Column(Integer, primary_key=True)
    started_at      = Column(DateTime, default=datetime.utcnow)
    stopped_at      = Column(DateTime, nullable=True)
    blocks_scanned  = Column(Integer, default=0)
    opportunities_found = Column(Integer, default=0)
    txs_success     = Column(Integer, default=0)
    txs_failed      = Column(Integer, default=0)
    total_profit_eth = Column(Float, default=0.0)
    stop_reason     = Column(String(128), nullable=True)
