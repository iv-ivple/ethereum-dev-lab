"""Read liquidation ratios (mat) from the MakerDAO Spot contract."""
import os
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

SPOT_ADDRESS = "0x65C79fcB50Ca1594B025960e539eD7A9a6D434A3"
SPOT_ABI = [
    {
        "name": "ilks",
        "type": "function",
        "inputs": [{"name": "ilk", "type": "bytes32"}],
        "outputs": [
            {"name": "pip", "type": "address"},   # oracle address
            {"name": "mat", "type": "uint256"},   # liquidation ratio (RAY)
        ],
    }
]

spot_contract = w3.eth.contract(address=SPOT_ADDRESS, abi=SPOT_ABI)
RAY = 10 ** 27

for ilk_name in ["ETH-A", "ETH-B", "ETH-C", "WBTC-A"]:
    ilk_bytes = ilk_name.encode().ljust(32, b'\x00')
    pip, mat = spot_contract.functions.ilks(ilk_bytes).call()
    mat_pct = mat / RAY * 100
    print(f"{ilk_name}: mat={mat_pct:.0f}%  oracle={pip}")
