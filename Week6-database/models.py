#!/usr/bin/env python3
"""
SQLAlchemy ORM models for blockchain data
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from datetime import datetime

Base = declarative_base()

class Wallet(Base):
    __tablename__ = 'wallets'
    
    id = Column(Integer, primary_key=True)
    address = Column(String, unique=True, nullable=False)
    label = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Wallet(address='{self.address}', label='{self.label}')>"

class Token(Base):
    __tablename__ = 'tokens'
    
    id = Column(Integer, primary_key=True)
    address = Column(String, unique=True, nullable=False)
    symbol = Column(String)
    name = Column(String)
    decimals = Column(Integer)
    total_supply = Column(Text)  # Store as string for large numbers
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    transfers = relationship('Transfer', back_populates='token')
    
    def __repr__(self):
        return f"<Token(symbol='{self.symbol}', name='{self.name}')>"

class Transfer(Base):
    __tablename__ = 'transfers'
    
    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, ForeignKey('tokens.id'), nullable=False)
    from_address = Column(String, nullable=False)
    to_address = Column(String, nullable=False)
    amount_raw = Column(Text, nullable=False)
    amount_decimal = Column(Text)
    block_number = Column(Integer, nullable=False)
    transaction_hash = Column(String, nullable=False)
    log_index = Column(Integer, nullable=False)
    timestamp = Column(Integer)
    gas_used = Column(Integer)
    
    # Relationship
    token = relationship('Token', back_populates='transfers')
    
    # Indexes
    __table_args__ = (
        Index('idx_transfers_token_block', 'token_id', 'block_number'),
        Index('idx_transfers_from', 'from_address'),
        Index('idx_transfers_to', 'to_address'),
        Index('idx_transfers_hash', 'transaction_hash'),
        Index('idx_unique_transfer', 'transaction_hash', 'log_index', unique=True),
    )
    
    def __repr__(self):
        return f"<Transfer(tx='{self.transaction_hash[:10]}...', amount='{self.amount_decimal}')>"

class Block(Base):
    __tablename__ = 'blocks'
    
    block_number = Column(Integer, primary_key=True)
    timestamp = Column(Integer, nullable=False)
    hash = Column(String, nullable=False)
    
    def __repr__(self):
        return f"<Block(number={self.block_number}, hash='{self.hash[:10]}...')>"

# Database connection helper
class DatabaseConnection:
    def __init__(self, db_path='sqlite:///databases/blockchain.db'):
        self.engine = create_engine(db_path, echo=False)
        self.Session = sessionmaker(bind=self.engine)
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)
        print("✅ Tables created using SQLAlchemy ORM")
    
    def get_session(self):
        """Get a new database session"""
        return self.Session()

if __name__ == '__main__':
    # Test the models
    db = DatabaseConnection()
    db.create_tables()
    
    # Test session
    session = db.get_session()
    print(f"✅ Database session created: {session}")
    session.close()
