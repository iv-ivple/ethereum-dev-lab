#!/usr/bin/env python3
"""
Connect to real ERC-20 tokens on Ethereum mainnet
"""
import json
import os
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv

# Load .env file from two levels up
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Your RPC endpoint (use your preferred provider)
# Using Cloudflare's free public Ethereum RPC endpoint as default
RPC_URL = os.getenv('RPC_URL', 'https://cloudflare-eth.com')

# Popular token addresses on Ethereum mainnet
TOKENS = {
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
}

# Minimal ERC-20 ABI
ERC20_ABI = json.loads('''
[
    {
        "constant": true,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]
''')

def connect_to_token(token_address):
    """Create a contract instance and fetch basic info"""
    # Connect to Ethereum
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Ethereum network")
        return None
    
    print(f"✅ Connected to Ethereum")
    print(f"   Latest block: {w3.eth.block_number:,}\n")
    
    # Create contract instance
    try:
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )
        
        # Fetch token metadata
        name = contract.functions.name().call()
        symbol = contract.functions.symbol().call()
        decimals = contract.functions.decimals().call()
        
        print(f"Token Information:")
        print(f"  Name: {name}")
        print(f"  Symbol: {symbol}")
        print(f"  Decimals: {decimals}")
        print(f"  Contract: {token_address}")
        
        return contract
        
    except Exception as e:
        print(f"❌ Error connecting to token: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("CONNECTING TO ERC-20 TOKENS")
    print("=" * 60)
    
    for name, address in TOKENS.items():
        print(f"\n--- {name} ---")
        connect_to_token(address)
        print()
