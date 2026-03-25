#!/usr/bin/env python3
"""
Fetch comprehensive ERC-20 token metadata
"""
import json
from web3 import Web3

RPC_URL = "https://eth.llamarpc.com"

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
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]
''')

POPULAR_TOKENS = {
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
    "LINK": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
}

def get_token_metadata(w3, token_address):
    """Fetch all metadata for an ERC-20 token"""
    try:
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )
        
        # Fetch all metadata
        name = contract.functions.name().call()
        symbol = contract.functions.symbol().call()
        decimals = contract.functions.decimals().call()
        total_supply_raw = contract.functions.totalSupply().call()
        
        # Format total supply
        total_supply = total_supply_raw / (10 ** decimals)
        
        return {
            'name': name,
            'symbol': symbol,
            'decimals': decimals,
            'total_supply_raw': total_supply_raw,
            'total_supply': total_supply,
            'contract_address': token_address,
            'error': None
        }
        
    except Exception as e:
        return {'error': str(e), 'contract_address': token_address}

def display_metadata(metadata):
    """Pretty print token metadata"""
    if metadata.get('error'):
        print(f"  ❌ Error: {metadata['error']}")
        return
    
    print(f"  Name: {metadata['name']}")
    print(f"  Symbol: {metadata['symbol']}")
    print(f"  Decimals: {metadata['decimals']}")
    print(f"  Total Supply: {metadata['total_supply']:,.2f} {metadata['symbol']}")
    print(f"  Contract: {metadata['contract_address']}")

def main():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    if not w3.is_connected():
        print("❌ Failed to connect")
        return
    
    print("=" * 60)
    print("ERC-20 TOKEN METADATA")
    print("=" * 60)
    
    for name, address in POPULAR_TOKENS.items():
        print(f"\n--- {name} ---")
        metadata = get_token_metadata(w3, address)
        display_metadata(metadata)

if __name__ == "__main__":
    main()
