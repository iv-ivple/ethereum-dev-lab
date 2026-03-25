#!/usr/bin/env python3
"""
get_eth_balance.py - Check ETH balance for any Ethereum address
"""

import os
import sys
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

RPC_URL = os.getenv('RPC_URL')

if not RPC_URL:
    raise ValueError("RPC_URL not found in .env file")

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    raise ConnectionError("Failed to connect to Ethereum node")

print("✓ Connected to Ethereum mainnet\n")

# Function to convert Wei to Ether
def wei_to_ether(wei_amount):
    """Convert Wei to Ether"""
    return w3.from_wei(wei_amount, 'ether')

# Function to check balance
def get_balance(address):
    """Get ETH balance for an address"""
    
    # Validate address format
    if not w3.is_address(address):
        raise ValueError(f"Invalid Ethereum address: {address}")
    
    # Convert to checksum address
    checksum_address = w3.to_checksum_address(address)
    
    # Get balance in Wei
    balance_wei = w3.eth.get_balance(checksum_address)
    
    # Convert to Ether
    balance_ether = wei_to_ether(balance_wei)
    
    return balance_wei, balance_ether

# Main execution
if __name__ == "__main__":
    # Example addresses (Ethereum Foundation, Vitalik's public address)
    example_addresses = [
        "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe",  # Ethereum Foundation
        "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Vitalik
    ]
    
    # Check if address provided as command line argument
    if len(sys.argv) > 1:
        addresses_to_check = [sys.argv[1]]
    else:
        print("No address provided. Checking example addresses...\n")
        addresses_to_check = example_addresses
    
    # Check balance for each address
    for address in addresses_to_check:
        try:
            wei, ether = get_balance(address)
            print(f"Address: {address}")
            print(f"  Balance (Wei):   {wei:,}")
            print(f"  Balance (Ether): {ether}")
            print()
        except ValueError as e:
            print(f"Error: {e}\n")
        except Exception as e:
            print(f"Unexpected error: {e}\n")

