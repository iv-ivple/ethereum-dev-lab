
from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

# Replace with a real arbitrage tx hash from Eigenphi
TX_HASH = "0xYOUR_ARB_TX_HASH_HERE"

ERC20_TRANSFER_TOPIC = Web3.keccak(text="Transfer(address,address,uint256)").hex()

receipt = w3.eth.get_transaction_receipt(TX_HASH)

print(f"Transaction: {TX_HASH}")
print(f"Gas Used: {receipt.gasUsed:,}")
print(f"\nTransfer Events:")

for log in receipt.logs:
    if len(log.topics) >= 3 and log.topics[0].hex() == ERC20_TRANSFER_TOPIC:
        from_addr = "0x" + log.topics[1].hex()[-40:]
        to_addr   = "0x" + log.topics[2].hex()[-40:]
        amount    = int(log.data.hex(), 16)
        token     = log.address
        print(f"  {from_addr[:10]}... → {to_addr[:10]}... | {amount} | Token: {token[:10]}...")
