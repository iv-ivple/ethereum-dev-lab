#!/usr/bin/env python3
"""
Fetch token transfers from blockchain and store in database
Integrates Week 5 event fetching with Week 6 database storage
"""

import sys
import os
from web3 import Web3
from db_helper import BlockchainDB

# Configuration
RPC_URL = os.getenv('ETH_RPC_URL', 'https://eth.llamarpc.com')
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# ERC-20 ABI (minimal)
ERC20_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    },
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
]

def fetch_and_store_transfers(token_address, start_block, end_block):
    """Fetch transfers and store in database"""
    
    db = BlockchainDB()
    
    # Get or add token
    contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
    
    try:
        symbol = contract.functions.symbol().call()
        name = contract.functions.name().call()
        decimals = contract.functions.decimals().call()
        
        # Store token info
        db.add_token(token_address, symbol, name, decimals)
        print(f"📝 Token: {name} ({symbol})")
        
    except Exception as e:
        print(f"❌ Error fetching token metadata: {e}")
        return
    
    # Fetch transfer events using get_logs instead of filter
    print(f"🔍 Fetching transfers from block {start_block} to {end_block}...")
    
    # Use get_logs directly - works with more RPC endpoints
    events = w3.eth.get_logs({
        'fromBlock': start_block,
        'toBlock': end_block,
        'address': Web3.to_checksum_address(token_address),
        'topics': [Web3.keccak(text='Transfer(address,address,uint256)').hex()]
    })
    
    print(f"📦 Found {len(events)} transfer events")
    
    # Store each transfer
    stored_count = 0
    for event in events:
        # Decode addresses from topics
        from_addr = '0x' + event['topics'][1].hex()[-40:]
        to_addr = '0x' + event['topics'][2].hex()[-40:]
        
        # Decode amount from data
        amount_raw = int(event['data'].hex(), 16)
        
        # Store transfer
        result = db.add_transfer(
            token_address=token_address,
            from_addr=from_addr,
            to_addr=to_addr,
            amount_raw=amount_raw,
            block_number=event['blockNumber'],
            tx_hash=event['transactionHash'].hex(),
            log_index=event['logIndex'],
            timestamp=None  # Could fetch from block
        )
        
        if result:
            stored_count += 1
            if stored_count % 10 == 0:
                print(f"   Stored {stored_count} transfers...")
    
    print(f"✅ Stored {stored_count} new transfers")
    
    # Show stats
    stats = db.get_stats()
    print(f"\n📊 Database Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python3 store_transfers.py <token_address> <start_block> <end_block>")
        print("\nExample (USDC recent transfers):")
        print("python3 scripts/week6/store_transfers.py 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 21500000 21500100")
        sys.exit(1)
    
    token_addr = sys.argv[1]
    start = int(sys.argv[2])
    end = int(sys.argv[3])
    
    fetch_and_store_transfers(token_addr, start, end)
