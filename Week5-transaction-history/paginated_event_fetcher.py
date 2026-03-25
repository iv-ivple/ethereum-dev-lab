import os
import time
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to Alchemy
RPC_URL = os.getenv('RPC_URL')
w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Verify connection
if not w3.is_connected():
    raise Exception("Failed to connect to Ethereum node")

print(f"Connected to Ethereum network")
print(f"Current block: {w3.eth.block_number}\n")

# ERC-20 Transfer event signature
TRANSFER_EVENT_SIGNATURE = w3.keccak(text="Transfer(address,address,uint256)").hex()


def fetch_events_paginated(
    token_address,
    wallet_address=None,
    start_block=None,
    end_block=None,
    chunk_size=2000,
    max_retries=3,
    retry_delay=1
):
    """
    Fetch ERC-20 Transfer events with pagination and error handling.
    
    Args:
        token_address: ERC-20 token contract address
        wallet_address: Optional wallet address to filter transfers (will filter both from/to)
        start_block: Starting block number
        end_block: Ending block number
        chunk_size: Number of blocks to fetch per request (Alchemy default: 2000)
        max_retries: Maximum number of retry attempts
        retry_delay: Delay in seconds between retries
    
    Returns:
        List of all event logs
    """
    all_events = []
    
    # Use recent blocks if not specified
    if end_block is None:
        end_block = w3.eth.block_number
    if start_block is None:
        start_block = end_block - 10000
    
    current_block = start_block
    total_blocks = end_block - start_block + 1
    blocks_processed = 0
    
    # Normalize token address
    token_address = Web3.to_checksum_address(token_address)
    
    print(f"Fetching Transfer events for token: {token_address}")
    if wallet_address:
        wallet_address = Web3.to_checksum_address(wallet_address)
        print(f"Wallet filter: {wallet_address}")
    print(f"Block range: {start_block} to {end_block} ({total_blocks:,} blocks)")
    print(f"Chunk size: {chunk_size} blocks")
    print("⚠️  Note: Alchemy Free tier limits eth_getLogs to 10 blocks per request")
    print("    This script will make many small requests. Consider upgrading for faster results.\n")
    
    while current_block <= end_block:
        to_block = min(current_block + chunk_size - 1, end_block)
        blocks_in_chunk = to_block - current_block + 1
        
        retry_count = 0
        current_chunk_size = chunk_size
        
        while retry_count < max_retries:
            try:
                # Create simple filter - just token address and event signature
                # We'll filter by wallet address after fetching
                filter_params = {
                    'fromBlock': current_block,
                    'toBlock': to_block,
                    'address': token_address,
                    'topics': [TRANSFER_EVENT_SIGNATURE]
                }
                
                # Fetch logs
                logs = w3.eth.get_logs(filter_params)
                
                # Filter by wallet address if specified
                if wallet_address:
                    filtered_logs = []
                    wallet_lower = wallet_address.lower()
                    
                    for log in logs:
                        # Extract from and to addresses from topics
                        from_addr = '0x' + log['topics'][1].hex()[-40:]
                        to_addr = '0x' + log['topics'][2].hex()[-40:]
                        
                        # Check if wallet is involved in either direction
                        if from_addr.lower() == wallet_lower or to_addr.lower() == wallet_lower:
                            filtered_logs.append(log)
                    
                    logs = filtered_logs
                
                all_events.extend(logs)
                
                # Update progress
                blocks_processed += blocks_in_chunk
                progress = (blocks_processed / total_blocks) * 100
                
                print(f"✓ Blocks {current_block:,} to {to_block:,} | "
                      f"Found {len(logs)} events | "
                      f"Progress: {progress:.1f}% "
                      f"({blocks_processed:,}/{total_blocks:,} blocks)")
                
                # Move to next chunk
                current_block = to_block + 1
                break  # Success, exit retry loop
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Print full error for debugging
                print(f"✗ Error fetching blocks {current_block} to {to_block}:")
                print(f"  Full error: {e}")
                
                # Try to get more details from the response
                if hasattr(e, 'response') and hasattr(e.response, 'text'):
                    print(f"  Response: {e.response.text}")
                
                # Handle "query returned more than X results" error
                if "query returned more than" in error_msg or "exceed maximum" in error_msg or "10000" in error_msg or "free tier" in error_msg or "block range" in error_msg:
                    current_chunk_size = max(current_chunk_size // 2, 10)  # Don't go below 10 for Alchemy free tier
                    current_chunk_size = current_chunk_size // 2
                    
                    if current_chunk_size < 10:
                        print(f"✗ Chunk size too small, skipping blocks {current_block} to {to_block}")
                        current_block = to_block + 1
                        break
                    
                    to_block = min(current_block + current_chunk_size - 1, end_block)
                    print(f"⚠ Too many results, reducing chunk size to {current_chunk_size}")
                    retry_count += 1
                    
                # Handle rate limiting
                elif "rate limit" in error_msg or "429" in error_msg:
                    wait_time = retry_delay * (2 ** retry_count)
                    print(f"⚠ Rate limited, waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    retry_count += 1
                    
                # Handle other errors
                else:
                    print(f"✗ Error fetching blocks {current_block} to {to_block}:")
                    print(f"  {e}")
                    retry_count += 1
                    
                    if retry_count < max_retries:
                        print(f"  Retrying ({retry_count}/{max_retries})...")
                        time.sleep(retry_delay)
                    else:
                        print(f"  Max retries reached, skipping this chunk")
                        current_block = to_block + 1
                        break
        
        # Small delay to avoid rate limits
        time.sleep(0.05)
    
    return all_events


def decode_transfer_event(log):
    """
    Decode a Transfer event log.
    
    Args:
        log: Raw event log from Web3
    
    Returns:
        Dictionary with decoded event data
    """
    return {
        'block_number': log['blockNumber'],
        'transaction_hash': log['transactionHash'].hex(),
        'from': '0x' + log['topics'][1].hex()[-40:],
        'to': '0x' + log['topics'][2].hex()[-40:],
        'value': int(log['data'].hex(), 16),
        'log_index': log['logIndex']
    }


def main():
    print("=" * 70)
    print("PAGINATED EVENT FETCHER - Day 5")
    print("=" * 70 + "\n")
    
    # Test 1: Fetch USDC transfers for a specific wallet
    print("TEST 1: Fetching USDC transfers for Binance wallet")
    print("-" * 70)
    
    USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    BINANCE_WALLET = "0x47ac0Fb4F2D84898e4D9E7b4DaB3C24507a6D503"
    
    current_block = w3.eth.block_number
    start_block = current_block - 100  # Just last ~20 minutes for free tier
    
    start_time = time.time()
    
    events = fetch_events_paginated(
        token_address=USDC_ADDRESS,
        wallet_address=BINANCE_WALLET,
        start_block=start_block,
        end_block=current_block,
        chunk_size=10  # Alchemy Free tier limit!
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Display results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Total events found: {len(events)}")
    print(f"Time taken: {duration:.2f} seconds")
    if events:
        print(f"Average speed: {len(events)/duration:.1f} events/second\n")
        
        print("First 5 events (decoded):")
        print("-" * 70)
        
        for i, log in enumerate(events[:5]):
            decoded = decode_transfer_event(log)
            value_usdc = decoded['value'] / 1e6  # USDC has 6 decimals
            
            direction = "OUT" if decoded['from'].lower() == BINANCE_WALLET.lower() else "IN"
            
            print(f"\nEvent {i+1}: [{direction}]")
            print(f"  Block: {decoded['block_number']:,}")
            print(f"  From: {decoded['from']}")
            print(f"  To: {decoded['to']}")
            print(f"  Amount: {value_usdc:,.2f} USDC")
            print(f"  Tx: {decoded['transaction_hash']}")
    else:
        print("No events found in this time range.")
        print("Try increasing the block range or using a more active wallet.\n")


if __name__ == "__main__":
    main()
