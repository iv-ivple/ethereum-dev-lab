# gas/tx_gas_profiler.py
from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

def profile_contract_gas(contract_address: str, block_range: int = 1000) -> dict:
    """
    Analyze gas usage for recent transactions to a contract.
    Returns statistics useful for optimizing your gas limit defaults.
    """
    latest = w3.eth.block_number
    from_block = latest - block_range
    
    logs = w3.eth.get_logs({
        "fromBlock": from_block,
        "toBlock": "latest",
        "address": contract_address,
    })
    
    tx_hashes = list({log["transactionHash"] for log in logs})[:50]  # cap at 50
    
    gas_used_list = []
    for txhash in tx_hashes:
        receipt = w3.eth.get_transaction_receipt(txhash)
        gas_used_list.append(receipt["gasUsed"])
    
    if not gas_used_list:
        return {"error": "No transactions found in range"}
    
    gas_used_list.sort()
    return {
        "tx_count": len(gas_used_list),
        "min": gas_used_list[0],
        "p50": gas_used_list[len(gas_used_list) // 2],
        "p90": gas_used_list[int(len(gas_used_list) * 0.9)],
        "p99": gas_used_list[int(len(gas_used_list) * 0.99)],
        "max": gas_used_list[-1],
        "recommended_limit": int(gas_used_list[int(len(gas_used_list) * 0.99)] * 1.15),
    }
