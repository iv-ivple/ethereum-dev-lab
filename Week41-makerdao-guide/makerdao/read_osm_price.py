"""
Read current and next price from the ETH-A OSM via raw storage slot reads.
(OSM.peek() is restricted to whitelisted callers on mainnet.)
"""
import os
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

OSM_ETH = "0x81FE72B5A8d1A857d176C3E7d5Bd2679A9B85763"

def read_osm_slot(osm_address, slot):
    raw = w3.eth.get_storage_at(osm_address, slot)
    val_bytes = raw[-16:]
    price = int.from_bytes(val_bytes, 'big')
    valid = raw[-17] == 1
    return price / 10**18, valid

current_price, current_valid = read_osm_slot(OSM_ETH, 3)
next_price,    next_valid    = read_osm_slot(OSM_ETH, 4)

print(f"OSM ETH-A:")
print(f"  Current price : ${current_price:,.2f}  (valid={current_valid})")
print(f"  Next price    : ${next_price:,.2f}  (valid={next_valid})")
print(f"  Note: 'next' becomes 'current' after the next hourly poke()")
