#!/usr/bin/env python3
"""
Creates the database schema for tracking blockchain data
"""

import sqlite3
import os

def create_schema(db_path='databases/blockchain.db'):
    """Create all necessary tables with proper schema"""
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute('PRAGMA foreign_keys = ON')
    
    # Create wallets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT NOT NULL UNIQUE,
            label TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create tokens table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT NOT NULL UNIQUE,
            symbol TEXT,
            name TEXT,
            decimals INTEGER,
            total_supply TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create transfers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_id INTEGER NOT NULL,
            from_address TEXT NOT NULL,
            to_address TEXT NOT NULL,
            amount_raw TEXT NOT NULL,
            amount_decimal REAL,
            block_number INTEGER NOT NULL,
            transaction_hash TEXT NOT NULL,
            log_index INTEGER NOT NULL,
            timestamp INTEGER,
            gas_used INTEGER,
            FOREIGN KEY (token_id) REFERENCES tokens(id),
            UNIQUE(transaction_hash, log_index)
        )
    ''')
    
    # Create blocks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocks (
            block_number INTEGER PRIMARY KEY,
            timestamp INTEGER NOT NULL,
            hash TEXT NOT NULL
        )
    ''')
    
    # Create indexes for performance
    print("Creating indexes...")
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_transfers_token 
        ON transfers(token_id, block_number)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_transfers_from 
        ON transfers(from_address)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_transfers_to 
        ON transfers(to_address)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_transfers_hash 
        ON transfers(transaction_hash)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_transfers_block 
        ON transfers(block_number)
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database schema created: {db_path}")
    print("   Tables: wallets, tokens, transfers, blocks")
    print("   Indexes: 5 indexes for query optimization")

if __name__ == '__main__':
    create_schema()
