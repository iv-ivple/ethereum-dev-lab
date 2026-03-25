#!/usr/bin/env python3
"""
Day 2: Fetching Transaction History
Demonstrates how to fetch Ethereum transaction history for an address
using block iteration and RPC provider limits handling.
"""

from web3 import Web3
from typing import List, Dict, Optional
import time

# Configuration
RPC_URL = "https://eth.llamarpc.com"  # Free public RPC endpoint
TEST_ADDRESS = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Vitalik's wallet
BLOCKS_TO_SCAN = 1000  # Number of recent blocks to scan
MAX_BLOCKS_PER_REQUEST = 100  # Batch size to avoid rate limits

class TransactionFetcher:
    """Handles fetching and displaying transaction history for an Ethereum address."""
    
    def __init__(self, rpc_url: str):
        """Initialize Web3 connection."""
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to Ethereum node at {rpc_url}")
        
        print(f"✓ Connected to Ethereum network")
        print(f"✓ Chain ID: {self.w3.eth.chain_id}")
        print()
    
    def get_latest_block(self) -> int:
        """Get the latest block number."""
        return self.w3.eth.block_number
    
    def fetch_transactions_in_range(
        self, 
        address: str, 
        start_block: int, 
        end_block: int
    ) -> List[Dict]:
        """
        Fetch all transactions for an address within a block range.
        
        Args:
            address: Ethereum address to search for
            start_block: Starting block number
            end_block: Ending block number
            
        Returns:
            List of transaction dictionaries
        """
        address = address.lower()
        transactions = []
        
        print(f"Scanning blocks {start_block} to {end_block}...")
        
        # Iterate through blocks in batches to respect rate limits
        for block_num in range(start_block, end_block + 1):
            try:
                # Fetch block with full transaction data
                block = self.w3.eth.get_block(block_num, full_transactions=True)
                
                # Check each transaction in the block
                for tx in block['transactions']:
                    tx_from = tx['from'].lower() if tx['from'] else None
                    tx_to = tx['to'].lower() if tx['to'] else None
                    
                    # Check if address is involved in the transaction
                    if tx_from == address or tx_to == address:
                        transactions.append({
                            'hash': tx['hash'].hex(),
                            'from': tx['from'],
                            'to': tx['to'],
                            'value': self.w3.from_wei(tx['value'], 'ether'),
                            'block_number': tx['blockNumber'],
                            'gas': tx['gas'],
                            'gas_price': self.w3.from_wei(tx['gasPrice'], 'gwei'),
                            'direction': 'OUT' if tx_from == address else 'IN'
                        })
                
                # Progress indicator (every 50 blocks)
                if (block_num - start_block + 1) % 50 == 0:
                    progress = ((block_num - start_block + 1) / (end_block - start_block + 1)) * 100
                    print(f"  Progress: {progress:.1f}% ({block_num - start_block + 1}/{end_block - start_block + 1} blocks)")
                
                # Small delay to avoid rate limiting
                time.sleep(0.05)
                
            except Exception as e:
                print(f"  Warning: Error fetching block {block_num}: {e}")
                continue
        
        return transactions
    
    def display_transactions(self, transactions: List[Dict]) -> None:
        """Display transactions in a readable format."""
        if not transactions:
            print("=" * 80)
            print("No transactions found in the specified block range.")
            print("=" * 80)
            return
        
        print()
        print("=" * 80)
        print(f"Found {len(transactions)} transaction(s)")
        print("=" * 80)
        
        for i, tx in enumerate(transactions, 1):
            print(f"\nTransaction #{i}")
            print(f"  Hash:        {tx['hash']}")
            print(f"  Direction:   {tx['direction']}")
            print(f"  From:        {tx['from']}")
            print(f"  To:          {tx['to']}")
            print(f"  Value:       {tx['value']:.6f} ETH")
            print(f"  Block:       {tx['block_number']}")
            print(f"  Gas Limit:   {tx['gas']}")
            print(f"  Gas Price:   {tx['gas_price']:.2f} Gwei")
            print("-" * 80)
    
    def fetch_recent_transactions(
        self, 
        address: str, 
        num_blocks: int = 1000
    ) -> List[Dict]:
        """
        Fetch recent transactions for an address.
        
        Args:
            address: Ethereum address to search
            num_blocks: Number of recent blocks to scan
            
        Returns:
            List of transactions
        """
        latest_block = self.get_latest_block()
        start_block = max(0, latest_block - num_blocks + 1)
        
        print(f"Latest block: {latest_block}")
        print(f"Scanning last {num_blocks} blocks (from block {start_block})")
        print(f"Target address: {address}")
        print()
        
        # Fetch transactions with rate limit handling
        all_transactions = []
        
        # Process in smaller batches to respect RPC limits
        for batch_start in range(start_block, latest_block + 1, MAX_BLOCKS_PER_REQUEST):
            batch_end = min(batch_start + MAX_BLOCKS_PER_REQUEST - 1, latest_block)
            
            batch_txs = self.fetch_transactions_in_range(
                address, 
                batch_start, 
                batch_end
            )
            all_transactions.extend(batch_txs)
            
            # Brief pause between batches
            if batch_end < latest_block:
                time.sleep(0.5)
        
        return all_transactions


def main():
    """Main execution function."""
    print("=" * 80)
    print("Ethereum Transaction History Fetcher")
    print("=" * 80)
    print()
    
    try:
        # Initialize fetcher
        fetcher = TransactionFetcher(RPC_URL)
        
        # Fetch transactions
        transactions = fetcher.fetch_recent_transactions(
            TEST_ADDRESS, 
            BLOCKS_TO_SCAN
        )
        
        # Display results
        fetcher.display_transactions(transactions)
        
        # Summary
        print()
        print("=" * 80)
        print("Summary")
        print("=" * 80)
        print(f"Blocks scanned:     {BLOCKS_TO_SCAN}")
        print(f"Transactions found: {len(transactions)}")
        
        if transactions:
            total_in = sum(tx['value'] for tx in transactions if tx['direction'] == 'IN')
            total_out = sum(tx['value'] for tx in transactions if tx['direction'] == 'OUT')
            print(f"Total ETH IN:       {total_in:.6f} ETH")
            print(f"Total ETH OUT:      {total_out:.6f} ETH")
        
        print("=" * 80)
        
    except ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check your internet connection")
        print("2. Try a different RPC endpoint")
        print("3. Ensure web3.py is installed: pip install web3")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
