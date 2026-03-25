"""
Day 4: Filtering ERC-20 Transfer Events
This script filters and decodes Transfer events for ERC-20 tokens.
"""

from web3 import Web3
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file two directories up
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(env_path)

# Connect to Ethereum node via Alchemy
RPC_URL = os.getenv('RPC_URL')
if not RPC_URL:
    print("❌ RPC_URL not found in .env file")
    print(f"   Looking for .env at: {env_path}")
    sys.exit(1)

w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Verify connection
if not w3.is_connected():
    print("❌ Failed to connect to Ethereum network")
    sys.exit(1)

print("✅ Connected to Ethereum Mainnet")
print(f"Current block: {w3.eth.block_number}\n")

# Transfer event signature: Transfer(address indexed from, address indexed to, uint256 value)
TRANSFER_EVENT_SIGNATURE = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

# Token contracts
TOKENS = {
    'USDC': {
        'address': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
        'decimals': 6,
        'symbol': 'USDC'
    },
    'DAI': {
        'address': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
        'decimals': 18,
        'symbol': 'DAI'
    }
}


def format_address(topic_hex):
    """Extract and format address from topic (32 bytes padded)"""
    if isinstance(topic_hex, bytes):
        return '0x' + topic_hex.hex()[-40:]
    return '0x' + topic_hex[-40:]


def decode_transfer_event(log, token_info):
    """Decode a Transfer event log"""
    try:
        # Extract addresses from indexed topics
        from_address = format_address(log['topics'][1])
        to_address = format_address(log['topics'][2])
        
        # Decode amount from data field
        amount_wei = int(log['data'].hex(), 16)
        amount = amount_wei / (10 ** token_info['decimals'])
        
        return {
            'from': from_address,
            'to': to_address,
            'amount': amount,
            'amount_wei': amount_wei,
            'block': log['blockNumber'],
            'tx_hash': log['transactionHash'].hex()
        }
    except Exception as e:
        print(f"Error decoding event: {e}")
        return None


def get_transfer_events(token_address, start_block, end_block, address_filter=None, direction='both'):
    """
    Fetch Transfer events for a token contract with chunking to avoid API limits
    
    Args:
        token_address: The ERC-20 token contract address
        start_block: Starting block number
        end_block: Ending block number
        address_filter: Optional address to filter (None for all transfers)
        direction: 'to', 'from', or 'both' (only used if address_filter is provided)
    """
    
    # Build topics based on filter
    if address_filter:
        # Pad address to 32 bytes (64 hex chars)
        padded_address = '0x' + address_filter[2:].lower().zfill(64)
        
        if direction == 'to':
            topics = [
                TRANSFER_EVENT_SIGNATURE,
                None,  # from (any)
                padded_address  # to (specific)
            ]
        elif direction == 'from':
            topics = [
                TRANSFER_EVENT_SIGNATURE,
                padded_address,  # from (specific)
                None  # to (any)
            ]
        else:  # both
            topics = [TRANSFER_EVENT_SIGNATURE]
    else:
        topics = [TRANSFER_EVENT_SIGNATURE]
    
    # Chunk requests to avoid API limits (2000 blocks per request)
    CHUNK_SIZE = 2000
    all_logs = []
    
    current_start = start_block
    total_chunks = (end_block - start_block + CHUNK_SIZE) // CHUNK_SIZE
    chunk_num = 0
    
    while current_start <= end_block:
        chunk_num += 1
        current_end = min(current_start + CHUNK_SIZE - 1, end_block)
        
        # Create filter parameters
        filter_params = {
            'fromBlock': current_start,
            'toBlock': current_end,
            'address': token_address,
            'topics': topics
        }
        
        try:
            print(f"   📦 Chunk {chunk_num}/{total_chunks}: blocks {current_start:,} to {current_end:,}...", end=' ', flush=True)
            logs = w3.eth.get_logs(filter_params)
            all_logs.extend(logs)
            print(f"✓ ({len(logs)} events)")
        except Exception as e:
            print(f"\n   ⚠️  Error: {str(e)[:100]}")
        
        current_start = current_end + 1
    
    return all_logs


def filter_transfers_by_address(logs, target_address, direction='both'):
    """Filter logs to only include transfers involving target address"""
    target_address = target_address.lower()
    filtered = []
    
    for log in logs:
        from_addr = format_address(log['topics'][1]).lower()
        to_addr = format_address(log['topics'][2]).lower()
        
        if direction == 'to' and to_addr == target_address:
            filtered.append(log)
        elif direction == 'from' and from_addr == target_address:
            filtered.append(log)
        elif direction == 'both' and (from_addr == target_address or to_addr == target_address):
            filtered.append(log)
    
    return filtered


def display_transfer(transfer, token_info, index):
    """Display a single transfer event"""
    print(f"\n{'='*80}")
    print(f"Transfer #{index + 1}")
    print(f"{'='*80}")
    print(f"Token:        {token_info['symbol']}")
    print(f"From:         {transfer['from']}")
    print(f"To:           {transfer['to']}")
    print(f"Amount:       {transfer['amount']:,.{token_info['decimals']}} {token_info['symbol']}")
    print(f"Block:        {transfer['block']}")
    print(f"Tx Hash:      {transfer['tx_hash']}")
    print(f"Etherscan:    https://etherscan.io/tx/{transfer['tx_hash']}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 filter_transfer_events.py <address> [blocks_to_scan]")
        print("Example: python3 filter_transfer_events.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 10000")
        sys.exit(1)
    
    target_address = sys.argv[1]
    blocks_to_scan = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
    
    # Validate address
    if not Web3.is_address(target_address):
        print("❌ Invalid Ethereum address")
        sys.exit(1)
    
    target_address = Web3.to_checksum_address(target_address)
    
    # Set block range (recent blocks)
    end_block = w3.eth.block_number
    start_block = end_block - blocks_to_scan
    
    print(f"\n{'='*80}")
    print(f"ERC-20 TRANSFER EVENT FILTER")
    print(f"{'='*80}")
    print(f"Target Address:  {target_address}")
    print(f"Block Range:     {start_block:,} to {end_block:,} ({blocks_to_scan:,} blocks)")
    print(f"{'='*80}\n")
    
    # Process each token
    all_transfers = []
    
    for token_name, token_info in TOKENS.items():
        print(f"\n📊 Analyzing {token_name} transfers...")
        print(f"Token Address: {token_info['address']}")
        
        # Fetch logs with chunking
        logs = get_transfer_events(
            token_info['address'],
            start_block,
            end_block
        )
        
        if not logs:
            print(f"   ℹ️  No Transfer events found for {token_name}")
            continue
        
        print(f"   ✅ Total: {len(logs)} Transfer events")
        
        # Filter for our target address
        filtered_logs = filter_transfers_by_address(logs, target_address, 'both')
        print(f"   🎯 Filtered: {len(filtered_logs)} transfers involving {target_address}")
        
        # Decode and store transfers
        for log in filtered_logs:
            transfer = decode_transfer_event(log, token_info)
            if transfer:
                transfer['token'] = token_name
                transfer['token_info'] = token_info
                all_transfers.append(transfer)
    
    # Display results
    print(f"\n\n{'='*80}")
    print(f"SUMMARY: Found {len(all_transfers)} transfers across all tokens")
    print(f"{'='*80}")
    
    if all_transfers:
        # Sort by block number
        all_transfers.sort(key=lambda x: x['block'])
        
        # Display each transfer
        for idx, transfer in enumerate(all_transfers):
            display_transfer(transfer, transfer['token_info'], idx)
        
        # Summary statistics
        print(f"\n\n{'='*80}")
        print(f"STATISTICS")
        print(f"{'='*80}")
        
        for token_name in TOKENS.keys():
            token_transfers = [t for t in all_transfers if t['token'] == token_name]
            if token_transfers:
                total_received = sum(t['amount'] for t in token_transfers if t['to'].lower() == target_address.lower())
                total_sent = sum(t['amount'] for t in token_transfers if t['from'].lower() == target_address.lower())
                
                print(f"\n{token_name}:")
                print(f"  Transfers: {len(token_transfers)}")
                print(f"  Received:  {total_received:,.6f} {token_name}")
                print(f"  Sent:      {total_sent:,.6f} {token_name}")
                print(f"  Net:       {total_received - total_sent:,.6f} {token_name}")
    else:
        print("\nℹ️  No transfers found for the specified address in the given block range.")
        print("   Try increasing the number of blocks to scan or check a different address.")


if __name__ == "__main__":
    main()
