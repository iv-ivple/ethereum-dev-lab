# gas/eip1559_model.py
from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

def get_fee_history(block_count: int = 10, percentiles: list = [10, 50, 90]):
    """
    Fetch historical base fees and priority fee percentiles.
    percentiles: which tip percentiles to return per block.
    """
    history = w3.eth.fee_history(block_count, "latest", percentiles)
    return history

def get_current_fees():
    """
    Returns base_fee (next block), suggested max_priority_fee, and
    a recommended max_fee_per_gas with a 2x base fee buffer.
    """
    latest = w3.eth.get_block("latest")
    base_fee = latest["baseFeePerGas"]  # in Wei

    # web3.py helper for suggested priority fee
    priority_fee = w3.eth.max_priority_fee  # in Wei

    # Standard: maxFee = 2 * baseFee + priorityFee
    # The 2x buffer protects against base fee spikes over ~6 consecutive blocks
    max_fee = 2 * base_fee + priority_fee

    return {
        "base_fee_gwei": Web3.from_wei(base_fee, "gwei"),
        "priority_fee_gwei": Web3.from_wei(priority_fee, "gwei"),
        "max_fee_gwei": Web3.from_wei(max_fee, "gwei"),
        "base_fee_wei": base_fee,
        "priority_fee_wei": priority_fee,
        "max_fee_wei": max_fee,
    }

def simulate_base_fee_trajectory(blocks_ahead: int = 6):
    """
    Model max possible base fee change over N blocks.
    Base fee can change by at most 12.5% per block.
    """
    fees = get_current_fees()
    base = fees["base_fee_wei"]
    trajectory = [base]
    for _ in range(blocks_ahead):
        base = int(base * 1.125)  # worst-case full blocks
        trajectory.append(base)
    return [Web3.from_wei(f, "gwei") for f in trajectory]

if __name__ == "__main__":
    fees = get_current_fees()
    print(f"Base fee:     {fees['base_fee_gwei']:.4f} Gwei")
    print(f"Priority fee: {fees['priority_fee_gwei']:.4f} Gwei")
    print(f"Max fee:      {fees['max_fee_gwei']:.4f} Gwei")
    print("\nWorst-case base fee trajectory (6 blocks):")
    for i, f in enumerate(simulate_base_fee_trajectory()):
        print(f"  Block +{i}: {f:.4f} Gwei")
