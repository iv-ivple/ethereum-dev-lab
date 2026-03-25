#!/usr/bin/env python3
"""
Query and analyze stored transfer data
"""

import sys
from db_helper import BlockchainDB
from tabulate import tabulate

def query_address_transfers(address):
    """Show transfers for an address"""
    db = BlockchainDB()
    
    transfers = db.get_transfers_for_address(address, limit=20)
    
    if not transfers:
        print(f"No transfers found for {address}")
        return
    
    print(f"\n🔍 Recent transfers for {address[:10]}...:\n")
    
    data = []
    for t in transfers:
        direction = "📤 OUT" if t.from_address.lower() == address.lower() else "📥 IN"
        data.append([
            t.block_number,
            direction,
            t.token.symbol,
            f"{float(t.amount_decimal):.6f}",
            t.transaction_hash[:10] + "..."
        ])
    
    print(tabulate(data, headers=['Block', 'Direction', 'Token', 'Amount', 'Tx Hash']))

def query_token_stats(token_symbol):
    """Show statistics for a token"""
    db = BlockchainDB()
    
    token = db.get_token_by_symbol(token_symbol)
    if not token:
        print(f"Token {token_symbol} not found in database")
        return
    
    print(f"\n📊 {token.name} ({token.symbol}) Statistics:\n")
    print(f"   Contract: {token.address}")
    print(f"   Decimals: {token.decimals}")
    print(f"   Total Supply: {token.total_supply}")
    
    transfers = db.get_transfers_for_token(token.address, limit=10)
    print(f"   Stored Transfers: {len(transfers)}")
    
    if transfers:
        print(f"\n   Recent transfers:")
        for t in transfers[:5]:
            print(f"      Block {t.block_number}: {t.amount_decimal} {token.symbol}")

if __name__ == '__main__':
    # Install tabulate if needed
    try:
        from tabulate import tabulate
    except ImportError:
        print("Installing tabulate...")
        import os
        os.system('pip3 install tabulate')
        from tabulate import tabulate
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Query address: python3 query_transfers.py address <ADDRESS>")
        print("  Query token:   python3 query_transfers.py token <SYMBOL>")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'address' and len(sys.argv) >= 3:
        query_address_transfers(sys.argv[2])
    elif cmd == 'token' and len(sys.argv) >= 3:
        query_token_stats(sys.argv[2])
    else:
        print("Invalid command")
