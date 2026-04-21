# gas/advanced_gas_calculator.py
from web3 import Web3
from gas.gas_oracle import get_gas_recommendation, get_network_congestion
from gas.tx_cost_estimator import get_eth_price_usd
import os
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

def calculate_arb_gas_cost(
    gas_units: int,
    speed: str = "fast",   # arb bots always want fast/instant
    verbose: bool = True
) -> dict:
    fees = get_gas_recommendation(speed)
    congestion = get_network_congestion()
    eth_price = get_eth_price_usd()
    
    cost_wei = gas_units * fees["max_fee_per_gas"]
    cost_eth = float(Web3.from_wei(cost_wei, "ether"))
    cost_usd = cost_eth * eth_price if eth_price else None
    
    if verbose:
        print(f"Network: {congestion.upper()} | Speed: {speed}")
        print(f"Gas units: {gas_units:,} | Max fee: {fees['max_fee_gwei']:.3f} Gwei")
        print(f"Cost: {cost_eth:.6f} ETH", end="")
        if cost_usd:
            print(f" (${cost_usd:.4f} USD)")
        else:
            print()
    
    return {
        "gas_units": gas_units,
        "cost_eth": cost_eth,
        "cost_usd": cost_usd,
        "congestion": congestion,
        "speed": speed,
        "max_fee_per_gas": fees["max_fee_per_gas"],
        "max_priority_fee_per_gas": fees["max_priority_fee_per_gas"],
    }
