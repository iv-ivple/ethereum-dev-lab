"""Compute annualised stability fees from the Jug contract."""
import os, datetime
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

JUG_ADDRESS = "0x19c0976f590D67707E62397C87829d896Dc0f1F"
JUG_ABI = [
    {
        "name": "ilks",
        "type": "function",
        "inputs": [{"name": "ilk", "type": "bytes32"}],
        "outputs": [
            {"name": "duty", "type": "uint256"},
            {"name": "rho",  "type": "uint256"},
        ],
    },
    {"name": "base", "type": "function", "inputs": [], "outputs": [{"name": "", "type": "uint256"}]},
]

jug = w3.eth.contract(address=JUG_ADDRESS, abi=JUG_ABI)
RAY = 10 ** 27
SECONDS_PER_YEAR = 31_536_000

base = jug.functions.base().call()
base_annual = ((base / RAY) ** SECONDS_PER_YEAR - 1) * 100
print(f"Base rate: {base_annual:.4f}% per year\n")
print(f"{'ILK':<10} {'Annual Stability Fee':>22} {'Last Drip':>20}")
print("-" * 55)

for ilk_name in ["ETH-A", "ETH-B", "ETH-C", "WBTC-A"]:
    ilk_bytes = ilk_name.encode().ljust(32, b'\x00')
    duty, rho = jug.functions.ilks(ilk_bytes).call()
    annual_fee = ((duty / RAY) ** SECONDS_PER_YEAR - 1) * 100 + base_annual
    last_drip = datetime.datetime.utcfromtimestamp(rho).strftime('%Y-%m-%d %H:%M')
    print(f"{ilk_name:<10} {annual_fee:>21.4f}% {last_drip:>20}")
