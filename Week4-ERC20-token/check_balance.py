#!/usr/bin/env python3
"""
Check ERC-20 token balances for addresses
"""
import json
import sys
from web3 import Web3

RPC_URL = "https://eth.llamarpc.com"

# Full ERC-20 ABI with balance functions
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
    },
    {
        "constant": true,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]
''')

# Example addresses (Vitalik's address and a whale)
EXAMPLE_ADDRESSES = {
    "Vitalik": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    "USDC Treasury": "0x5414d89a8bF7E99d732BC52f3e6A3Ef461c0C078",
}

def format_token_amount(raw_balance, decimals):
    """Convert raw balance to human-readable format"""
    return raw_balance / (10 ** decimals)

def check_token_balance(w3, token_address, wallet_address):
    """Check balance of a specific token for an address"""
    try:
        # Create contract instance
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )
        
        # Fetch token info
        symbol = contract.functions.symbol().call()
        decimals = contract.functions.decimals().call()
        
        # Fetch balance
        raw_balance = contract.functions.balanceOf(
            Web3.to_checksum_address(wallet_address)
        ).call()
        
        # Format balance
        formatted_balance = format_token_amount(raw_balance, decimals)
        
        return {
            'symbol': symbol,
            'decimals': decimals,
            'raw_balance': raw_balance,
            'formatted_balance': formatted_balance
        }
        
    except Exception as e:
        return {'error': str(e)}

def main():
    # Connect to Ethereum
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Ethereum")
        return
    
    print("=" * 60)
    print("ERC-20 TOKEN BALANCE CHECKER")
    print("=" * 60)
    
    # USDC contract
    usdc_address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    
    for name, address in EXAMPLE_ADDRESSES.items():
        print(f"\n{name}: {address}")
        
        result = check_token_balance(w3, usdc_address, address)
        
        if 'error' in result:
            print(f"  ❌ Error: {result['error']}")
        else:
            print(f"  Symbol: {result['symbol']}")
            print(f"  Raw Balance: {result['raw_balance']:,}")
            print(f"  Formatted: {result['formatted_balance']:,.2f} {result['symbol']}")
    
    # Allow user input
    if len(sys.argv) > 1:
        custom_address = sys.argv[1]
        print(f"\n--- Custom Address ---")
        print(f"Address: {custom_address}")
        result = check_token_balance(w3, usdc_address, custom_address)
        if 'error' not in result:
            print(f"Balance: {result['formatted_balance']:,.2f} {result['symbol']}")

if __name__ == "__main__":
    main()
    print("\nUsage: python3 check_balance.py [ADDRESS]")

