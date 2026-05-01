from web3 import Web3
from eth_account import Account
from keeper.config import config

def sign_tx(tx: dict, w3: Web3) -> str:
    """Signs a tx dict and returns the raw hex transaction."""
    # Estimate gas and update the limit
    estimated_gas = w3.eth.estimate_gas(tx)
    tx["gas"] = int(estimated_gas * 1.15)   # 15% buffer

    signed = Account.sign_transaction(tx, private_key=config.private_key)
    return signed.rawTransaction.hex()
