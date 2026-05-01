# gas/multicall_batcher.py
from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

MULTICALL3_ADDRESS = "0xcA11bde05977b3631167028862bE2a173976CA11"
MULTICALL3_ABI = [
    {
        "inputs": [{"components": [
            {"name": "target", "type": "address"},
            {"name": "allowFailure", "type": "bool"},
            {"name": "callData", "type": "bytes"}
        ], "name": "calls", "type": "tuple[]"}],
        "name": "aggregate3",
        "outputs": [{"components": [
            {"name": "success", "type": "bool"},
            {"name": "returnData", "type": "bytes"}
        ], "name": "returnData", "type": "tuple[]"}],
        "stateMutability": "payable",
        "type": "function"
    }
]

ERC20_BALANCE_OF_SIG = "0x70a08231"  # balanceOf(address)

def batch_balance_check(token_address: str, wallets: list[str]) -> dict:
    """
    Fetch ERC-20 balances for multiple wallets in a single RPC call.
    Saves N-1 round trips compared to individual calls.
    """
    multicall = w3.eth.contract(address=MULTICALL3_ADDRESS, abi=MULTICALL3_ABI)
    
    calls = []
    for wallet in wallets:
        # Encode balanceOf(wallet) calldata manually
        padded = wallet[2:].lower().zfill(64)
        calldata = ERC20_BALANCE_OF_SIG + padded
        calls.append((token_address, False, bytes.fromhex(calldata[2:])))
    
    results = multicall.functions.aggregate3(calls).call()
    
    balances = {}
    for wallet, (success, data) in zip(wallets, results):
        if success and len(data) == 32:
            balance = int(data.hex(), 16)
            balances[wallet] = balance
        else:
            balances[wallet] = None
    return balances
