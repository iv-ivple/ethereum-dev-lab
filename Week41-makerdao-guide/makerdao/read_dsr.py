"""Read the current DAI Savings Rate from the Pot contract."""
import os
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

POT_ADDRESS = "0x197E90f9FAD81970bA7976f33CbD77088E5D7cf"
POT_ABI = [
    {"name": "dsr", "type": "function", "inputs": [], "outputs": [{"name": "", "type": "uint256"}]},
    {"name": "Pie", "type": "function", "inputs": [], "outputs": [{"name": "", "type": "uint256"}]},
    {"name": "chi", "type": "function", "inputs": [], "outputs": [{"name": "", "type": "uint256"}]},
]

pot = w3.eth.contract(address=POT_ADDRESS, abi=POT_ABI)
RAY = 10 ** 27
SECONDS_PER_YEAR = 31_536_000

dsr = pot.functions.dsr().call()
pie = pot.functions.Pie().call()
chi = pot.functions.chi().call()

annual_dsr = ((dsr / RAY) ** SECONDS_PER_YEAR - 1) * 100
total_locked = (pie * chi / RAY) / 10**18

print(f"DAI Savings Rate (DSR) : {annual_dsr:.4f}% per year")
print(f"Total DAI in DSR       : {total_locked:,.0f} DAI")
