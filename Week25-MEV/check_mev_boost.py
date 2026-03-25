
from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

block_number = w3.eth.block_number - 10  # recent finalised block
block = w3.eth.get_block(block_number)

extra_data = block['extraData'].decode('utf-8', errors='replace')
fee_recipient = block['miner']

print(f"Block: {block_number}")
print(f"Fee Recipient: {fee_recipient}")
print(f"Extra Data (raw): {block['extraData'].hex()}")
print(f"Extra Data (text): {extra_data}")
print(f"Gas Used: {block.gasUsed:,} / {block.gasLimit:,} ({block.gasUsed/block.gasLimit*100:.1f}%)")
