# scripts/mempool_peek.py
from web3 import Web3
import os, time
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

# Note: eth_getBlockByNumber with 'pending' shows the pending block
pending = w3.eth.get_block('pending', full_transactions=True)
txs = pending.transactions[:10]  # first 10

for tx in txs:
    print(f"Hash: {tx.hash.hex()}")
    print(f"  From:     {tx['from']}")
    print(f"  To:       {tx.to}")
    print(f"  Value:    {w3.from_wei(tx.value, 'ether'):.4f} ETH")
    print(f"  Gas Price:{w3.from_wei(tx.gasPrice, 'gwei'):.2f} Gwei")
    print()
