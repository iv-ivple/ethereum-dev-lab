#!/usr/bin/env python3
"""
Sign Ethereum transactions (without sending them).
Demonstrates nonce management and transaction structure.
"""

from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def get_nonce(w3, address):
    """Get the current nonce (transaction count) for an address."""
    return w3.eth.get_transaction_count(address)

def sign_transaction(w3, private_key, to_address, value_eth, gas_price_gwei=None):
    """
    Sign a transaction without broadcasting it.
    
    Args:
        w3: Web3 instance
        private_key: Sender's private key
        to_address: Recipient address
        value_eth: Amount in ETH
        gas_price_gwei: Gas price in Gwei (optional, will estimate if not provided)
    """
    account = Account.from_key(private_key)
    
    # Get current nonce
    nonce = get_nonce(w3, account.address)
    
    # Get gas price
    if gas_price_gwei is None:
        gas_price = w3.eth.gas_price
    else:
        gas_price = w3.to_wei(gas_price_gwei, 'gwei')
    
    # Build transaction
    transaction = {
        'nonce': nonce,
        'to': to_address,
        'value': w3.to_wei(value_eth, 'ether'),
        'gas': 21000,  # Standard ETH transfer gas limit
        'gasPrice': gas_price,
        'chainId': w3.eth.chain_id
    }
    
    # Sign transaction
    signed_txn = account.sign_transaction(transaction)
    
    return {
        'transaction': transaction,
        'signed_transaction': signed_txn,
        'raw_transaction': signed_txn.raw_transaction.hex(),
        'transaction_hash': signed_txn.hash.hex()
    }

def main():
    print("=" * 70)
    print("TRANSACTION SIGNING (OFFLINE)")
    print("=" * 70)
    print()
    
    # Connect to Ethereum (read-only for nonce and gas price)
    rpc_url = os.getenv('RPC_URL', 'https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY')
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Ethereum node")
        print("   Update INFURA_URL in your .env file")
        return
    
    print(f"✅ Connected to Ethereum Mainnet (Chain ID: {w3.eth.chain_id})")
    print()
    
    # Create test account
    account = Account.create()
    
    print(f"Test Sender: {account.address}")
    print()
    
    # Example transaction parameters
    to_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"  # Example address (corrected)
    value_eth = 0.001
    
    print(f"📤 Transaction Details:")
    print(f"   To:     {to_address}")
    print(f"   Amount: {value_eth} ETH")
    print()
    
    # Get nonce
    nonce = get_nonce(w3, account.address)
    print(f"🔢 Current Nonce: {nonce}")
    print(f"   (This is transaction #{nonce} from this address)")
    print()
    
    # Estimate gas price
    gas_price_wei = w3.eth.gas_price
    gas_price_gwei = w3.from_wei(gas_price_wei, 'gwei')
    print(f"⛽ Current Gas Price: {gas_price_gwei:.2f} Gwei")
    print()
    
    # Sign transaction (but don't send!)
    print("✍️  Signing transaction...")
    result = sign_transaction(
        w3, 
        account.key.hex(), 
        to_address, 
        value_eth
    )
    
    print()
    print(f"✅ Transaction Signed!")
    print(f"   Transaction Hash: {result['transaction_hash']}")
    print(f"   Raw Transaction:  {result['raw_transaction'][:66]}...")
    print()
    
    print("=" * 70)
    print("💡 Key Concepts:")
    print("  • Nonce: Prevents replay attacks, must increment sequentially")
    print("  • Signing ≠ Sending: Signed transactions can be broadcast later")
    print("  • Gas Price: Higher = faster confirmation (but more expensive)")
    print("  • Chain ID: Prevents transactions from working on wrong network")
    print()
    print("⚠️  This transaction was NOT sent to the network!")
    print("=" * 70)

if __name__ == "__main__":
    main()

