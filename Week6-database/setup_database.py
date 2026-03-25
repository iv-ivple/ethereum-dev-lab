#!/usr/bin/env python3
"""
Query and analyze stored transfer data
"""

import sys
from db_helper import BlockchainDB

# Try to import tabulate, install if needed
try:
    from tabulate import tabulate
except ImportError:
    print("Installing tabulate...")
    import os
    os.system('pip3 install tabulate')
    from tabulate import tabulate

def format_amount(amount, decimals=6):
    """Format amount with appropriate precision"""
    try:
        val = float(amount)
        if val == 0:
            return "0"
        elif val < 0.000001:
            return f"{val:.10f}".rstrip('0').rstrip('.')
        elif val < 1:
            return f"{val:.6f}".rstrip('0').rstrip('.')
        else:
            return f"{val:,.2f}"
    except (ValueError, TypeError):
        return str(amount)

def format_large_number(num):
    """Format large numbers with commas"""
    try:
        return f"{int(num):,}"
    except (ValueError, TypeError):
        return str(num)

def query_address_transfers(address):
    """Show transfers for an address"""
    try:
        db = BlockchainDB()
        
        # Validate address format (basic check)
        if not address.startswith('0x') or len(address) != 42:
            print(f"⚠️  Warning: '{address}' doesn't look like a valid Ethereum address")
            print("   Expected format: 0x... (42 characters)")
            response = input("   Continue anyway? (y/n): ")
            if response.lower() != 'y':
                return
        
        transfers = db.get_transfers_for_address(address, limit=20)
        
        if not transfers:
            print(f"No transfers found for {address}")
            return
        
        print(f"\n🔍 Recent transfers for {address[:10]}...:\n")
        
        data = []
        for t in transfers:
            # Determine direction and counterparty
            addr_lower = address.lower()
            if t.from_address.lower() == addr_lower:
                direction = "📤 OUT"
                counterparty = t.to_address[:10] + "..."
            elif t.to_address.lower() == addr_lower:
                direction = "📥 IN"
                counterparty = t.from_address[:10] + "..."
            else:
                direction = "❓"
                counterparty = "N/A"
            
            data.append([
                t.block_number,
                direction,
                counterparty,
                t.token.symbol,
                format_amount(t.amount_decimal),
                t.transaction_hash[:10] + "..."
            ])
        
        print(tabulate(data, headers=['Block', 'Dir', 'Counterparty', 'Token', 'Amount', 'Tx Hash']))
        print(f"\nShowing {len(transfers)} most recent transfers")
        
    except Exception as e:
        print(f"❌ Error querying address: {e}")
        import traceback
        traceback.print_exc()

def query_token_stats(token_symbol):
    """Show statistics for a token"""
    try:
        db = BlockchainDB()
        
        token = db.get_token_by_symbol(token_symbol)
        if not token:
            print(f"Token {token_symbol} not found in database")
            return
        
        print(f"\n📊 {token.name} ({token.symbol}) Statistics:\n")
        print(f"   Contract: {token.address}")
        print(f"   Decimals: {token.decimals}")
        
        if token.total_supply:
            formatted_supply = format_large_number(token.total_supply)
            print(f"   Total Supply: {formatted_supply}")
        
        transfers = db.get_transfers_for_token(token.address, limit=10)
        print(f"   Stored Transfers: {len(transfers)}")
        
        if transfers:
            print(f"\n   Recent transfers:")
            for t in transfers[:5]:
                amount_str = format_amount(t.amount_decimal)
                print(f"      Block {t.block_number}: {amount_str} {token.symbol}")
                
    except Exception as e:
        print(f"❌ Error querying token: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
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
        sys.exit(1)
