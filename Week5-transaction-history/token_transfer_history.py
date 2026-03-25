#!/usr/bin/env python3
"""
Token Transfer History CSV Generator
Fetches ERC-20 token transfer events for a wallet and generates a CSV report.
"""

import argparse
import csv
import sys
from datetime import datetime
from typing import List, Dict, Optional
from web3 import Web3
from web3.exceptions import Web3Exception

# Popular token addresses on Ethereum mainnet
POPULAR_TOKENS = {
    'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
    'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
    'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
    'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
    'WBTC': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
    'LINK': '0x514910771AF9Ca656af840dff83E8264EcF986CA',
    'UNI': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984',
    'SHIB': '0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE',
}

# ERC-20 Transfer event signature
TRANSFER_EVENT_SIGNATURE = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'

# Standard ERC-20 ABI for decimals and symbol
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]


class TokenTransferFetcher:
    def __init__(self, rpc_url: str):
        """Initialize Web3 connection."""
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to Ethereum node")
        print(f"✓ Connected to Ethereum node")
        print(f"✓ Current block: {self.w3.eth.block_number:,}\n")

    def get_token_info(self, token_address: str) -> Dict[str, any]:
        """Get token symbol and decimals."""
        try:
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=ERC20_ABI
            )
            symbol = contract.functions.symbol().call()
            decimals = contract.functions.decimals().call()
            return {'symbol': symbol, 'decimals': decimals}
        except Exception as e:
            print(f"⚠ Warning: Could not fetch token info for {token_address}: {e}")
            return {'symbol': 'UNKNOWN', 'decimals': 18}

    def fetch_transfer_events(
        self,
        wallet_address: str,
        token_address: str,
        from_block: int,
        to_block: int,
        token_info: Dict[str, any]
    ) -> List[Dict]:
        """Fetch all Transfer events for a wallet and token with adaptive batching."""
        wallet_address = Web3.to_checksum_address(wallet_address)
        token_address = Web3.to_checksum_address(token_address)
        
        print(f"Fetching {token_info['symbol']} transfers from block {from_block:,} to {to_block:,}...")
        
        all_logs = []
        current_from = from_block
        total_blocks = to_block - from_block
        batch_size = 1000  # Start with 1000 blocks
        
        while current_from <= to_block:
            current_to = min(current_from + batch_size - 1, to_block)
            blocks_processed = current_from - from_block
            progress = (blocks_processed / total_blocks) * 100 if total_blocks > 0 else 100
            
            print(f"  Batch: blocks {current_from:,} to {current_to:,} (size: {batch_size}) [{progress:.1f}%]", end='\r')
            
            filter_params = {
                'fromBlock': current_from,
                'toBlock': current_to,
                'address': token_address,
                'topics': [TRANSFER_EVENT_SIGNATURE]
            }
            
            try:
                logs = self.w3.eth.get_logs(filter_params)
                all_logs.extend(logs)
                
                # Success! Move to next batch and try increasing batch size
                current_from = current_to + 1
                if batch_size < 1000:
                    batch_size = min(batch_size * 2, 1000)  # Gradually increase back to 1000
                    
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a "too many results" error
                if 'max results' in error_msg or 'query exceeds' in error_msg:
                    # Extract suggested range if provided
                    if 'retry with the range' in error_msg:
                        try:
                            # Parse: "retry with the range 23979854-23980344"
                            range_part = error_msg.split('retry with the range')[1].strip().strip("'\"")
                            suggested_end = int(range_part.split('-')[1])
                            new_batch_size = suggested_end - current_from + 1
                            batch_size = max(10, new_batch_size)  # Use suggested size, min 10 blocks
                            print(f"\n  ℹ Reducing batch size to {batch_size} blocks due to result limit")
                        except:
                            # If parsing fails, just reduce batch size by half
                            batch_size = max(10, batch_size // 2)
                            print(f"\n  ℹ Reducing batch size to {batch_size} blocks")
                    else:
                        # Generic reduction
                        batch_size = max(10, batch_size // 2)
                        print(f"\n  ℹ Reducing batch size to {batch_size} blocks")
                    # Don't advance current_from, retry with smaller batch
                    
                else:
                    # Different error, skip this batch and continue
                    print(f"\n⚠ Warning: Error fetching logs for blocks {current_from:,}-{current_to:,}: {e}")
                    current_from = current_to + 1
        
        print(f"\n  Fetched {len(all_logs)} total transfer events")
        
        logs = all_logs
        
        transfers = []
        relevant_logs = []
        
        # Normalize wallet address for comparison
        wallet_addr_lower = wallet_address.lower()
        
        # Filter logs that involve our wallet
        for log in logs:
            # topic[1] is 'from', topic[2] is 'to' (both padded to 32 bytes)
            # Handle both HexBytes and strings
            topic1 = log['topics'][1]
            topic2 = log['topics'][2]
            
            # Convert to hex string if needed
            if hasattr(topic1, 'hex'):
                topic1_hex = topic1.hex()
            else:
                topic1_hex = topic1 if isinstance(topic1, str) else str(topic1)
            
            if hasattr(topic2, 'hex'):
                topic2_hex = topic2.hex()
            else:
                topic2_hex = topic2 if isinstance(topic2, str) else str(topic2)
            
            # Remove 0x prefix if present and take last 40 characters
            from_addr = '0x' + topic1_hex.replace('0x', '')[-40:].lower()
            to_addr = '0x' + topic2_hex.replace('0x', '')[-40:].lower()
            
            if from_addr == wallet_addr_lower or to_addr == wallet_addr_lower:
                relevant_logs.append((log, from_addr, to_addr))
        
        print(f"Found {len(relevant_logs)} relevant transfer events")
        
        # Debug: show first few addresses if no matches found
        if len(relevant_logs) == 0 and len(logs) > 0:
            print(f"\n  Debug: Wallet address we're looking for: {wallet_addr_lower}")
            print(f"  Debug: Sample of addresses in events:")
            for i, log in enumerate(logs[:3]):
                topic1 = log['topics'][1]
                topic2 = log['topics'][2]
                if hasattr(topic1, 'hex'):
                    topic1_hex = topic1.hex()
                else:
                    topic1_hex = topic1 if isinstance(topic1, str) else str(topic1)
                if hasattr(topic2, 'hex'):
                    topic2_hex = topic2.hex()
                else:
                    topic2_hex = topic2 if isinstance(topic2, str) else str(topic2)
                from_addr = '0x' + topic1_hex.replace('0x', '')[-40:].lower()
                to_addr = '0x' + topic2_hex.replace('0x', '')[-40:].lower()
                print(f"    Event {i+1}: from={from_addr}, to={to_addr}")
            print()
        
        if not relevant_logs:
            return []
        
        # Process each relevant log
        for i, (log, from_addr, to_addr) in enumerate(relevant_logs, 1):
            if i % 10 == 0 or i == len(relevant_logs):
                print(f"Processing event {i}/{len(relevant_logs)}...", end='\r')
            
            try:
                # Decode amount from data field
                data = log['data']
                if hasattr(data, 'hex'):
                    data_hex = data.hex()
                else:
                    data_hex = data if isinstance(data, str) else data.hex()
                
                # Remove 0x prefix if present
                data_hex = data_hex.replace('0x', '')
                amount_wei = int(data_hex, 16) if data_hex else 0
                amount = amount_wei / (10 ** token_info['decimals'])
                
                # Determine direction
                direction = 'OUT' if from_addr.lower() == wallet_address.lower() else 'IN'
                
                # Get transaction details
                tx_hash = log['transactionHash'].hex()
                block_number = log['blockNumber']
                
                # Get block timestamp
                block = self.w3.eth.get_block(block_number)
                timestamp = datetime.fromtimestamp(block['timestamp'])
                
                # Get transaction fee
                tx = self.w3.eth.get_transaction(tx_hash)
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                gas_used = receipt['gasUsed']
                gas_price = tx['gasPrice']
                tx_fee_wei = gas_used * gas_price
                tx_fee_eth = self.w3.from_wei(tx_fee_wei, 'ether')
                
                transfers.append({
                    'Timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'Block_Number': block_number,
                    'Tx_Hash': tx_hash,
                    'Token_Symbol': token_info['symbol'],
                    'Token_Address': token_address,
                    'Direction': direction,
                    'From': from_addr,
                    'To': to_addr,
                    'Amount': f"{amount:.{token_info['decimals']}}f".rstrip('0').rstrip('.'),
                    'Tx_Fee_ETH': float(tx_fee_eth)
                })
                
            except Exception as e:
                print(f"\n⚠ Warning: Error processing log at block {log['blockNumber']}: {e}")
                continue
        
        print(f"\n✓ Processed {len(transfers)} transfers for {token_info['symbol']}\n")
        return transfers

    def generate_csv(self, transfers: List[Dict], output_file: str):
        """Generate CSV file from transfer data."""
        if not transfers:
            print("No transfers to write to CSV")
            return
        
        headers = [
            'Timestamp',
            'Block_Number',
            'Tx_Hash',
            'Token_Symbol',
            'Token_Address',
            'Direction',
            'From',
            'To',
            'Amount',
            'Tx_Fee_ETH'
        ]
        
        # Sort by block number (oldest first)
        transfers.sort(key=lambda x: x['Block_Number'])
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(transfers)
        
        print(f"✓ CSV generated: {output_file}")
        print(f"✓ Total transfers: {len(transfers)}")
        
        # Print summary statistics
        incoming = sum(1 for t in transfers if t['Direction'] == 'IN')
        outgoing = sum(1 for t in transfers if t['Direction'] == 'OUT')
        print(f"  - Incoming: {incoming}")
        print(f"  - Outgoing: {outgoing}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate CSV of token transfer history for a wallet address',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single token, last 5000 blocks
  python3 token_transfer_history.py --address 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --token USDC --last-blocks 5000
  
  # Multiple tokens
  python3 token_transfer_history.py --address 0xYOUR_ADDRESS --tokens USDC,DAI,WETH --last-blocks 10000
  
  # Custom block range
  python3 token_transfer_history.py --address 0xYOUR_ADDRESS --token USDC --from-block 18000000 --to-block 18100000
  
  # Custom token address
  python3 token_transfer_history.py --address 0xYOUR_ADDRESS --token 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
        """
    )
    
    parser.add_argument(
        '--address',
        required=True,
        help='Wallet address to fetch transfers for'
    )
    
    parser.add_argument(
        '--token',
        help='Single token symbol (USDC, DAI, etc.) or contract address'
    )
    
    parser.add_argument(
        '--tokens',
        help='Comma-separated token symbols or addresses (USDC,DAI,WETH)'
    )
    
    parser.add_argument(
        '--from-block',
        type=int,
        help='Starting block number'
    )
    
    parser.add_argument(
        '--to-block',
        type=int,
        help='Ending block number (defaults to latest)'
    )
    
    parser.add_argument(
        '--last-blocks',
        type=int,
        help='Fetch last N blocks'
    )
    
    parser.add_argument(
        '--output',
        default='token_transfers.csv',
        help='Output CSV filename (default: token_transfers.csv)'
    )
    
    parser.add_argument(
        '--rpc-url',
        default='https://eth.llamarpc.com',
        help='Ethereum RPC URL (default: https://eth.llamarpc.com)'
    )
    
    return parser.parse_args()


def resolve_token_addresses(token_input: Optional[str]) -> List[str]:
    """Resolve token symbols or addresses to addresses."""
    if not token_input:
        return []
    
    tokens = [t.strip() for t in token_input.split(',')]
    addresses = []
    
    for token in tokens:
        if token.startswith('0x'):
            # It's an address
            addresses.append(token)
        else:
            # It's a symbol
            token_upper = token.upper()
            if token_upper in POPULAR_TOKENS:
                addresses.append(POPULAR_TOKENS[token_upper])
            else:
                print(f"⚠ Warning: Unknown token symbol '{token}', skipping")
    
    return addresses


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Validate wallet address
    if not args.address.startswith('0x') or len(args.address) != 42:
        print("✗ Error: Invalid wallet address format")
        sys.exit(1)
    
    # Determine which tokens to fetch
    token_addresses = []
    
    if args.token:
        token_addresses = resolve_token_addresses(args.token)
    elif args.tokens:
        token_addresses = resolve_token_addresses(args.tokens)
    else:
        print("✗ Error: Must specify either --token or --tokens")
        sys.exit(1)
    
    if not token_addresses:
        print("✗ Error: No valid token addresses found")
        sys.exit(1)
    
    try:
        # Initialize fetcher
        fetcher = TokenTransferFetcher(args.rpc_url)
        
        # Determine block range
        latest_block = fetcher.w3.eth.block_number
        
        if args.from_block and args.to_block:
            from_block = args.from_block
            to_block = args.to_block
        elif args.last_blocks:
            from_block = max(0, latest_block - args.last_blocks)
            to_block = latest_block
        else:
            # Default: last 10000 blocks
            from_block = max(0, latest_block - 10000)
            to_block = latest_block
        
        print(f"Wallet: {args.address}")
        print(f"Block range: {from_block:,} to {to_block:,} ({to_block - from_block:,} blocks)")
        print(f"Tokens: {len(token_addresses)}\n")
        
        # Fetch transfers for all tokens
        all_transfers = []
        
        for token_address in token_addresses:
            token_info = fetcher.get_token_info(token_address)
            transfers = fetcher.fetch_transfer_events(
                args.address,
                token_address,
                from_block,
                to_block,
                token_info
            )
            all_transfers.extend(transfers)
        
        # Generate CSV
        if all_transfers:
            fetcher.generate_csv(all_transfers, args.output)
        else:
            print("✗ No transfers found for the specified parameters")
            sys.exit(1)
        
    except ConnectionError as e:
        print(f"✗ Connection Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
