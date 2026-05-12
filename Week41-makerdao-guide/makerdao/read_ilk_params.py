"""
Read live ilk (collateral type) parameters from the MakerDAO Vat contract.
Requires: RPC_URL in .env
"""
import os
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

VAT_ADDRESS = "0x35D1b3F3D7966A1DFe207aa4514C12a259A0492B"
VAT_ABI = [
    {
        "name": "ilks",
        "type": "function",
        "inputs": [{"name": "ilk", "type": "bytes32"}],
        "outputs": [
            {"name": "Art",  "type": "uint256"},  # total normalised debt
            {"name": "rate", "type": "uint256"},  # stability fee accumulator
            {"name": "spot", "type": "uint256"},  # collateral price / safety margin
            {"name": "line", "type": "uint256"},  # debt ceiling
            {"name": "dust", "type": "uint256"},  # minimum debt
        ],
    }
]

vat = w3.eth.contract(address=VAT_ADDRESS, abi=VAT_ABI)
RAY = 10 ** 27
WAD = 10 ** 18
ILKS = ["ETH-A", "ETH-B", "ETH-C", "WBTC-A"]

print(f"{'ILK':<10} {'Total Debt (DAI)':>20} {'Rate':>12} {'Spot ($)':>12} {'Ceiling (M)':>14} {'Dust (DAI)':>12}")
print("-" * 85)

for ilk_name in ILKS:
    ilk_bytes = ilk_name.encode().ljust(32, b'\x00')
    Art, rate, spot, line, dust = vat.functions.ilks(ilk_bytes).call()

    total_debt_dai = (Art * rate / RAY) / WAD
    rate_pct = (rate / RAY - 1) * 100
    spot_usd = spot / RAY
    ceiling_m = (line / RAY) / WAD / 1_000_000
    dust_dai = dust / RAY / WAD

    print(f"{ilk_name:<10} {total_debt_dai:>20,.0f} {rate_pct:>11.4f}% {spot_usd:>12,.2f} {ceiling_m:>13,.1f}M {dust_dai:>12,.0f}")
