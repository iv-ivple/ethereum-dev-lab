"""Read a specific Vault's collateral, debt, and collateralisation ratio."""
import os
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

VAT_ADDRESS = "0x35D1b3F3D7966A1DFe207aa4514C12a259A0492B"
VAT_ABI = [
    {
        "name": "urns",
        "type": "function",
        "inputs": [{"name": "ilk", "type": "bytes32"}, {"name": "usr", "type": "address"}],
        "outputs": [{"name": "ink", "type": "uint256"}, {"name": "art", "type": "uint256"}],
    },
    {
        "name": "ilks",
        "type": "function",
        "inputs": [{"name": "ilk", "type": "bytes32"}],
        "outputs": [
            {"name": "Art", "type": "uint256"},
            {"name": "rate", "type": "uint256"},
            {"name": "spot", "type": "uint256"},
            {"name": "line", "type": "uint256"},
            {"name": "dust", "type": "uint256"},
        ],
    }
]

vat = w3.eth.contract(address=VAT_ADDRESS, abi=VAT_ABI)
WAD = 10 ** 18
RAY = 10 ** 27

# Find vault owners via: https://makerburn.com/#/vaults
VAULT_OWNER = "0xdDb108893104dE4E1C6d0E47b42Ca4D4Ec7d95d"
ILK = "ETH-A"
ilk_bytes = ILK.encode().ljust(32, b'\x00')

ink, art = vat.functions.urns(ilk_bytes, VAULT_OWNER).call()
_, rate, spot, _, _ = vat.functions.ilks(ilk_bytes).call()

collateral = ink / WAD
debt_dai   = (art * rate / RAY) / WAD
collat_value = collateral * (spot / RAY)
ratio = (collat_value / debt_dai * 100) if debt_dai > 0 else float('inf')
safe  = ink * spot >= art * rate  # Vat unsafe check

print(f"Vault: {ILK} / {VAULT_OWNER}")
print(f"  Collateral (ETH) : {collateral:,.4f}")
print(f"  Debt (DAI)       : {debt_dai:,.2f}")
print(f"  Collat ratio     : {ratio:.1f}%")
print(f"  Safe?            : {'Yes' if safe else 'NO — can be liquidated!'}")
