#!/usr/bin/env python3
"""
Week 4 Deliverable: Comprehensive ERC-20 Token Balance Checker

Features:
- Works with any ERC-20 token address
- Fetches token metadata (name, symbol, decimals, total supply)
- Checks balances for one or multiple addresses
- Handles errors gracefully
- User-friendly output with proper formatting
"""

import json
import sys
from web3 import Web3

# RPC Configuration
RPC_URL = "https://eth.llamarpc.com"  # Change to your preferred RPC

# Complete ERC-20 ABI
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

# Popular tokens for quick testing
POPULAR_TOKENS = {
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
    "LINK": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
}

# Example addresses for testing
EXAMPLE_ADDRESSES = {
    "Vitalik": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    "USDC Treasury": "0x5414d89a8bF7E99d732BC52f3e6A3Ef461c0C078",
}


class ERC20BalanceChecker:
    """Main class for checking ERC-20 token balances"""
    
    def __init__(self, rpc_url=RPC_URL):
        """Initialize Web3 connection"""
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to Ethereum network")
        print(f"✅ Connected to Ethereum (Block: {self.w3.eth.block_number:,})\n")
    
    def validate_address(self, address):
        """Validate Ethereum address"""
        try:
            return Web3.to_checksum_address(address)
        except Exception:
            return None
    
    def get_token_metadata(self, token_address):
        """Fetch token metadata"""
        try:
            contract = self.w3.eth.contract(
                address=self.validate_address(token_address),
                abi=ERC20_ABI
            )
            
            metadata = {
                'name': contract.functions.name().call(),
                'symbol': contract.functions.symbol().call(),
                'decimals': contract.functions.decimals().call(),
                'total_supply_raw': contract.functions.totalSupply().call(),
                'contract_address': token_address,
            }
            
            # Calculate formatted total supply
            metadata['total_supply'] = (
                metadata['total_supply_raw'] / (10 ** metadata['decimals'])
            )
            
            return metadata
            
        except Exception as e:
            return {'error': f"Failed to fetch metadata: {e}"}
    
    def get_balance(self, token_address, wallet_address):
        """Get token balance for a specific address"""
        try:
            contract = self.w3.eth.contract(
                address=self.validate_address(token_address),
                abi=ERC20_ABI
            )
            
            decimals = contract.functions.decimals().call()
            raw_balance = contract.functions.balanceOf(
                self.validate_address(wallet_address)
            ).call()
            
            formatted_balance = raw_balance / (10 ** decimals)
            
            return {
                'raw': raw_balance,
                'formatted': formatted_balance,
                'decimals': decimals
            }
            
        except Exception as e:
            return {'error': f"Failed to fetch balance: {e}"}
    
    def display_token_info(self, metadata):
        """Pretty print token metadata"""
        if 'error' in metadata:
            print(f"❌ {metadata['error']}")
            return
        
        print("📊 TOKEN INFORMATION")
        print("=" * 60)
        print(f"Name:          {metadata['name']}")
        print(f"Symbol:        {metadata['symbol']}")
        print(f"Decimals:      {metadata['decimals']}")
        print(f"Total Supply:  {metadata['total_supply']:,.2f} {metadata['symbol']}")
        print(f"Contract:      {metadata['contract_address']}")
        print()
    
    def display_balance(self, address, balance, symbol):
        """Pretty print balance information"""
        if 'error' in balance:
            print(f"  ❌ {balance['error']}")
            return
        
        print(f"  Address:   {address}")
        print(f"  Raw:       {balance['raw']:,}")
        print(f"  Balance:   {balance['formatted']:,.6f} {symbol}")
        print()
    
    def check_multiple_balances(self, token_address, addresses):
        """Check balances for multiple addresses"""
        # First, get token metadata
        metadata = self.get_token_metadata(token_address)
        self.display_token_info(metadata)
        
        if 'error' in metadata:
            return
        
        # Then check each address
        print("💰 BALANCES")
        print("=" * 60)
        
        for name, address in addresses.items():
            if not self.validate_address(address):
                print(f"❌ Invalid address for {name}: {address}\n")
                continue
            
            print(f"--- {name} ---")
            balance = self.get_balance(token_address, address)
            self.display_balance(address, balance, metadata['symbol'])


def print_usage():
    """Print usage instructions"""
    print("""
Usage:
  python3 erc20_balance_checker.py <token_address> <wallet_address> [wallet_address2...]
  python3 erc20_balance_checker.py <token_name> <wallet_address> [wallet_address2...]
  python3 erc20_balance_checker.py --examples

Examples:
  # Check USDC balance for Vitalik
  python3 erc20_balance_checker.py USDC 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
  
  # Check DAI balances for multiple addresses
  python3 erc20_balance_checker.py DAI 0xd8dA... 0xAb5801a7...
  
  # Use full token address
  python3 erc20_balance_checker.py 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 0xd8dA...
  
  # Run with example addresses
  python3 erc20_balance_checker.py --examples

Supported token shortcuts: USDC, DAI, WETH, UNI, LINK
""")


def main():
    """Main entry point"""
    print("=" * 60)
    print("ERC-20 TOKEN BALANCE CHECKER")
    print("=" * 60)
    print()
    
    # Handle command line arguments
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help']:
        print_usage()
        return
    
    # Initialize checker
    try:
        checker = ERC20BalanceChecker()
    except ConnectionError as e:
        print(f"❌ {e}")
        return
    
    # Handle --examples flag
    if sys.argv[1] == '--examples':
        print("Running with example addresses...\n")
        token_address = POPULAR_TOKENS['USDC']
        checker.check_multiple_balances(token_address, EXAMPLE_ADDRESSES)
        return
    
    # Get token address (either name or full address)
    token_input = sys.argv[1].upper()
    if token_input in POPULAR_TOKENS:
        token_address = POPULAR_TOKENS[token_input]
        print(f"Using {token_input} token\n")
    else:
        token_address = sys.argv[1]
    
    # Validate token address
    if not checker.validate_address(token_address):
        print(f"❌ Invalid token address: {token_address}")
        return
    
    # Get wallet addresses
    if len(sys.argv) < 3:
        print("❌ Please provide at least one wallet address")
        print_usage()
        return
    
    wallet_addresses = {}
    for i, addr in enumerate(sys.argv[2:], 1):
        wallet_addresses[f"Address {i}"] = addr
    
    # Check balances
    checker.check_multiple_balances(token_address, wallet_addresses)


if __name__ == "__main__":
    main()
