from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

# Approximate gas costs per operation (in gas units)
GAS_COSTS = {
    "erc20_transfer": 21_000 + 65_000,   # base + token transfer
    "uniswap_v2_swap": 110_000,            # single V2 swap
    "uniswap_v3_swap": 130_000,            # single V3 swap (more complex tick math)
}

def estimate_gas_for_path(num_hops: int, dex_type: str = "v2") -> int:
    """Estimate total gas units for a multi-hop arbitrage path."""
    swap_cost = GAS_COSTS[f"uniswap_{dex_type}_swap"]
    return swap_cost * num_hops

def get_current_gas_price() -> dict:
    """Fetch EIP-1559 fee data for accurate gas cost estimation."""
    fee_history = w3.eth.fee_history(5, "latest", [50])
    base_fee = w3.eth.get_block("latest")["baseFeePerGas"]
    # Median priority fee from last 5 blocks
    priority_fees = [block[0] for block in fee_history["reward"]]
    median_priority = sorted(priority_fees)[len(priority_fees) // 2]

    return {
        "base_fee_gwei": w3.from_wei(base_fee, "gwei"),
        "priority_fee_gwei": w3.from_wei(median_priority, "gwei"),
        "max_fee_gwei": w3.from_wei(base_fee + median_priority, "gwei"),
        "base_fee_wei": base_fee,
        "priority_fee_wei": median_priority,
    }

def calculate_gas_cost_eth(gas_units: int) -> float:
    """Return gas cost in ETH at current network prices."""
    prices = get_current_gas_price()
    total_wei = gas_units * (prices["base_fee_wei"] + prices["priority_fee_wei"])
    return w3.from_wei(total_wei, "ether")

if __name__ == "__main__":
    # Example: 3-hop V2 arbitrage
    gas_units = estimate_gas_for_path(num_hops=3, dex_type="v2")
    gas_cost = calculate_gas_cost_eth(gas_units)
    prices = get_current_gas_price()

    print(f"Estimated gas units:     {gas_units:,}")
    print(f"Base fee:                {prices['base_fee_gwei']:.2f} gwei")
    print(f"Priority fee:            {prices['priority_fee_gwei']:.2f} gwei")
    print(f"Max fee:                 {prices['max_fee_gwei']:.2f} gwei")
    print(f"Estimated gas cost:      {gas_cost:.6f} ETH")
