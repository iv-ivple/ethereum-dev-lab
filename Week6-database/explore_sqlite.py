#!/usr/bin/env python3
"""
Demonstrates basic SQLite operations in Python
"""

import sqlite3
from datetime import datetime

def main():
    # Connect to database (creates file if doesn't exist)
    conn = sqlite3.connect('databases/practice.db')
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS addresses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT NOT NULL UNIQUE,
            label TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert data
    test_addresses = [
        ('0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb', 'Uniswap Router'),
        ('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 'USDC Contract'),
    ]
    
    cursor.executemany(
        'INSERT OR IGNORE INTO addresses (address, label) VALUES (?, ?)',
        test_addresses
    )
    
    # Query data
    cursor.execute('SELECT * FROM addresses')
    rows = cursor.fetchall()
    
    print("Stored Addresses:")
    for row in rows:
        print(f"  ID: {row[0]}, Address: {row[1]}, Label: {row[2]}")
    
    # Commit changes and close
    conn.commit()
    conn.close()
    print("\nDatabase operations completed!")

if __name__ == '__main__':
    main()
