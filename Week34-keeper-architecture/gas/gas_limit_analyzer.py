# gas/gas_limit_analyzer.py
from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

def estimate_with_buffer(tx: dict, buffer_pct: float = 0.2) -> dict:
    """
    Estimate gas for a transaction and apply a safety buffer.
    Returns both the raw estimate and the buffered limit.
    """
    estimated = w3.eth.estimate_gas(tx)
    buffered = int(estimated * (1 + buffer_pct))
    return {
        "estimated": estimated,
        "buffered": buffered,
        "buffer_pct": buffer_pct * 100,
    }

def analyze_failed_tx(tx_hash: str):
    """
    Inspect a failed transaction to determine if it was out-of-gas.
    A tx is OOG if gasUsed == gasLimit (all gas consumed).
    """
    tx = w3.eth.get_transaction(tx_hash)
    receipt = w3.eth.get_transaction_receipt(tx_hash)

    oog = receipt["gasUsed"] == tx["gas"]
    return {
        "status": receipt["status"],  # 0 = failed
        "gas_limit": tx["gas"],
        "gas_used": receipt["gasUsed"],
        "out_of_gas": oog,
        "utilization_pct": (receipt["gasUsed"] / tx["gas"]) * 100,
    }

def build_access_list_tx(contract_address: str, data: str, sender: str):
    """
    Use eth_createAccessList to pre-declare storage slots.
    EIP-2930 access lists reduce cold SLOAD cost from 2100 to 100.
    """
    result = w3.eth.create_access_list({
        "from": sender,
        "to": contract_address,
        "data": data,
    })
    return result
