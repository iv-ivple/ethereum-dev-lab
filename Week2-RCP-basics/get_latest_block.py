#!/usr/bin/env python3
"""
get_latest_block.py - Fetch the latest block from Ethereum mainnet
"""

import os
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get RPC URL from environment
RPC_URL = os.getenv('RPC_URL')

if not RPC_URL:
    raise ValueError("RPC_URL not found in .env file")

# Initialize Web3 connection
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Check if connected
if not w3.is_connected():
    raise ConnectionError("Failed to connect to Ethereum node")

print("✓ Connected to Ethereum mainnet")

# Get latest block number
latest_block_number = w3.eth.block_number
print(f"\nLatest block number: {latest_block_number}")

# Get latest block details
latest_block = w3.eth.get_block('latest')

print(f"\nBlock Details:")
print(f"  Hash: {latest_block['hash'].hex()}")
print(f"  Timestamp: {latest_block['timestamp']}")
print(f"  Transactions: {len(latest_block['transactions'])}")
print(f"  Gas Used: {latest_block['gasUsed']:,}")
print(f"  Gas Limit: {latest_block['gasLimit']:,}")
print(f"  Miner: {latest_block['miner']}")
