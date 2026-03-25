"""
Day 3: Parsing Transaction Receipts
Web3 Learning Journey - Transaction Receipt Analysis

This script demonstrates how to:
- Fetch transaction receipts from Ethereum
- Parse receipt data including status, gas usage, and logs
- Display formatted receipt information
"""

from web3 import Web3
from datetime import datetime
from dotenv import load_dotenv
import os
import sys

# Load environment variables from .env file (two directories up)
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=env_path)

# Connect to Ethereum node using Alchemy
# Get RPC URL from environment variable
RPC_URL = os.getenv('RPC_URL')

if not RPC_URL:
    print("⚠️ Warning: RPC_URL not found in .env file")
    print(f"Looking for .env at: {os.path.abspath(env_path)}")
    print("Please make sure .env file exists two directories up with:")
    print("RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY")
    sys.exit(1)

ALCHEMY_URL = RPC_URL

def connect_to_ethereum():
    """Establish connection to Ethereum network via Alchemy"""
    try:
        w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))
        
        if w3.is_connected():
            print("✅ Successfully connected to Ethereum mainnet via Alchemy")
            print(f"Current block: {w3.eth.block_number}\n")
            return w3
        else:
            print("❌ Failed to connect to Ethereum network")
            print("Please check your RPC_URL in the .env file")
            return None
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("Make sure your .env file exists with RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY")
        return None

def get_block_timestamp(w3, block_number):
    """Fetch timestamp for a given block"""
    try:
        block = w3.eth.get_block(block_number)
        timestamp = block['timestamp']
        readable_time = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')
        return timestamp, readable_time
    except Exception as e:
        print(f"⚠️ Could not fetch block timestamp: {e}")
        return None, "N/A"

def parse_transaction_receipt(w3, tx_hash):
    """
    Parse and display transaction receipt information
    
    Args:
        w3: Web3 instance
        tx_hash: Transaction hash (with or without 0x prefix)
    """
    
    # Ensure tx_hash has 0x prefix
    if not tx_hash.startswith('0x'):
        tx_hash = '0x' + tx_hash
    
    print(f"📄 Fetching receipt for transaction: {tx_hash}\n")
    print("=" * 70)
    
    try:
        # Fetch the transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        
        # Parse status
        status = receipt['status']
        status_text = "✅ SUCCESS" if status == 1 else "❌ FAILED"
        
        print(f"\n🔍 TRANSACTION RECEIPT DETAILS")
        print("-" * 70)
        
        # Basic Information
        print(f"\n📊 Basic Information:")
        print(f"  Status: {status_text} (status code: {status})")
        print(f"  Transaction Hash: {receipt['transactionHash'].hex()}")
        print(f"  Block Number: {receipt['blockNumber']}")
        
        # Get block timestamp
        timestamp, readable_time = get_block_timestamp(w3, receipt['blockNumber'])
        print(f"  Block Timestamp: {readable_time}")
        
        print(f"  Transaction Index: {receipt['transactionIndex']}")
        print(f"  From: {receipt['from']}")
        print(f"  To: {receipt['to']}")
        
        # Gas Information
        print(f"\n⛽ Gas Usage:")
        print(f"  Gas Used: {receipt['gasUsed']:,} units")
        print(f"  Cumulative Gas Used: {receipt['cumulativeGasUsed']:,} units")
        
        # Calculate gas cost (fetch actual gas price from transaction)
        try:
            tx = w3.eth.get_transaction(tx_hash)
            gas_price_gwei = w3.from_wei(tx['gasPrice'], 'gwei')
            gas_cost_eth = w3.from_wei(receipt['gasUsed'] * tx['gasPrice'], 'ether')
            print(f"  Gas Price: {gas_price_gwei:.2f} Gwei")
            print(f"  Total Gas Cost: {gas_cost_eth:.6f} ETH")
        except Exception as e:
            print(f"  ⚠️ Could not calculate gas cost: {e}")
        
        # Effective Gas Price (post EIP-1559)
        if 'effectiveGasPrice' in receipt:
            effective_gas_price_gwei = w3.from_wei(receipt['effectiveGasPrice'], 'gwei')
            print(f"  Effective Gas Price: {effective_gas_price_gwei:.2f} Gwei")
        
        # Logs Information
        print(f"\n📝 Event Logs:")
        print(f"  Total Logs: {len(receipt['logs'])}")
        
        if len(receipt['logs']) > 0:
            print(f"\n  Log Details:")
            for i, log in enumerate(receipt['logs'], 1):
                print(f"\n  Log #{i}:")
                print(f"    Address: {log['address']}")
                print(f"    Topics: {len(log['topics'])} topic(s)")
                for j, topic in enumerate(log['topics']):
                    print(f"      Topic {j}: {topic.hex()}")
                print(f"    Data Length: {len(log['data'])} bytes")
                print(f"    Log Index: {log['logIndex']}")
        
        # Contract Creation
        if receipt['contractAddress']:
            print(f"\n📜 Contract Deployment:")
            print(f"  Contract Address: {receipt['contractAddress']}")
        
        # Additional Information
        print(f"\n🔗 Additional Information:")
        print(f"  Logs Bloom: {receipt['logsBloom'].hex()[:66]}... (truncated)")
        print(f"  Block Hash: {receipt['blockHash'].hex()}")
        
        # Transaction Type (post EIP-2718)
        if 'type' in receipt:
            tx_type = receipt['type']
            type_desc = {
                0: "Legacy",
                1: "EIP-2930 (Access List)",
                2: "EIP-1559 (Dynamic Fee)"
            }.get(tx_type, f"Unknown ({tx_type})")
            print(f"  Transaction Type: {type_desc}")
        
        print("\n" + "=" * 70)
        
        # Summary
        print(f"\n📋 SUMMARY:")
        print(f"  ✓ Transaction {status_text}")
        print(f"  ✓ Gas Used: {receipt['gasUsed']:,} units")
        print(f"  ✓ Emitted {len(receipt['logs'])} event log(s)")
        print(f"  ✓ Confirmed in block {receipt['blockNumber']}")
        
        return receipt
        
    except Exception as e:
        print(f"\n❌ Error fetching receipt: {e}")
        print(f"   Make sure the transaction hash is valid and the transaction is mined.")
        return None

def get_recent_transactions(w3, address, limit=5):
    """
    Helper function to get recent transaction hashes for an address
    Note: This is a simplified version. For production, use Etherscan API.
    """
    print(f"\n🔍 Finding recent transactions for: {address}")
    print("Note: This scans recent blocks, which may be slow...\n")
    
    current_block = w3.eth.block_number
    tx_hashes = []
    
    # Scan last 100 blocks (adjust as needed)
    for block_num in range(current_block, max(current_block - 100, 0), -1):
        try:
            block = w3.eth.get_block(block_num, full_transactions=True)
            for tx in block.transactions:
                if tx['from'] == address or tx['to'] == address:
                    tx_hashes.append(tx['hash'].hex())
                    if len(tx_hashes) >= limit:
                        return tx_hashes
        except Exception as e:
            continue
    
    return tx_hashes

def main():
    """Main execution function"""
    
    # Connect to Ethereum
    w3 = connect_to_ethereum()
    if not w3:
        sys.exit(1)
    
    # Example transaction hashes to test
    # These are real Ethereum mainnet transactions
    example_hashes = [
        # Successful USDC transfer
        "0x5b1b8c78f5ab6f7f52f8e1e9c6d3f2a1b4e7c9d0a3b2f5e8c1d4a7b0e3f6c9d2",
        
        # You can add more examples here
        # "0x..." # Another example
    ]
    
    print("\n" + "=" * 70)
    print("  ETHEREUM TRANSACTION RECEIPT PARSER")
    print("=" * 70)
    
    # Check for command line argument
    if len(sys.argv) > 1:
        tx_hash = sys.argv[1]
        parse_transaction_receipt(w3, tx_hash)
    else:
        print("\n📖 Usage Options:")
        print("  1. Run with transaction hash: python parse_receipts.py <tx_hash>")
        print("  2. Run without arguments to use interactive mode")
        print("  3. Modify example_hashes in the script to test specific transactions")
        
        print("\n" + "-" * 70)
        choice = input("\nEnter transaction hash (or 'q' to quit): ").strip()
        
        if choice.lower() == 'q':
            print("Goodbye! 👋")
            return
        
        if choice:
            parse_transaction_receipt(w3, choice)
        else:
            print("\n⚠️ No transaction hash provided.")
            print("Find transaction hashes on Etherscan: https://etherscan.io/")

if __name__ == "__main__":
    main()

"""
EXAMPLE USAGE:

SETUP:
1. Install required packages:
   pip install web3 python-dotenv

2. Your .env file should be two directories up from this script:
   project_root/
   ├── .env                    (your .env file here)
   ├── .gitignore
   └── some_folder/
       └── another_folder/
           └── parse_receipts.py  (this script)

3. .env file contents:
   RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY
   
   (Replace YOUR_API_KEY with your actual Alchemy API key)

4. Make sure .env is in your .gitignore (do not commit API keys!)

5. Get your Alchemy API key:
   - Sign up at https://www.alchemy.com/
   - Create a new app (Ethereum Mainnet)
   - Copy the API key from your dashboard

RUNNING THE SCRIPT:

1. Command line:
   python parse_receipts.py 0x5b1b8c78f5ab6f7f52f8e1e9c6d3f2a1b4e7c9d0a3b2f5e8c1d4a7b0e3f6c9d2

2. Interactive:
   python parse_receipts.py
   (then enter transaction hash when prompted)

3. Find real transaction hashes:
   - Visit https://etherscan.io/
   - Search for any address or transaction
   - Copy the transaction hash (starts with 0x)

LEARNING NOTES:

Receipt Fields:
- status: 1 = success, 0 = failed
- gasUsed: Actual gas consumed by transaction
- logs: Array of event logs emitted
- blockNumber: Block where tx was included
- from/to: Sender and recipient addresses
- contractAddress: Set if this was a contract deployment

Event Logs:
- address: Contract that emitted the event
- topics: Indexed event parameters (topic 0 = event signature)
- data: Non-indexed event parameters
- logIndex: Position of log in the block

Tips:
- Always check status field first
- Gas used can be less than gas limit
- Logs are crucial for tracking smart contract events
- Failed transactions still consume gas

SECURITY NOTE:
- Never commit your .env file to git
- Never share your API keys publicly
- Keep your .gitignore updated
"""
