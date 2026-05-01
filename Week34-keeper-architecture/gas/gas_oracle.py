# gas/gas_oracle.py
from web3 import Web3
import statistics
import os
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

SPEED_PROFILES = {
    "slow":    {"percentile": 10, "base_fee_multiplier": 1.0},
    "standard":{"percentile": 50, "base_fee_multiplier": 1.1},
    "fast":    {"percentile": 75, "base_fee_multiplier": 1.2},
    "instant": {"percentile": 90, "base_fee_multiplier": 1.3},
}

def get_gas_recommendation(speed: str = "standard") -> dict:
    """
    Returns EIP-1559 gas parameters for a given speed profile.
    Uses fee_history to pick a priority fee at the target percentile.
    """
    if speed not in SPEED_PROFILES:
        raise ValueError(f"speed must be one of {list(SPEED_PROFILES.keys())}")
    
    profile = SPEED_PROFILES[speed]
    percentile = profile["percentile"]
    
    history = w3.eth.fee_history(10, "latest", [percentile])
    tips = [r[0] for r in history["reward"] if r]  # tip at chosen percentile
    median_tip = int(statistics.median(tips))
    
    latest = w3.eth.get_block("latest")
    base_fee = latest["baseFeePerGas"]
    buffered_base = int(base_fee * profile["base_fee_multiplier"])
    max_fee = buffered_base + median_tip
    
    return {
        "speed": speed,
        "max_priority_fee_per_gas": median_tip,
        "max_fee_per_gas": max_fee,
        "base_fee": base_fee,
        "priority_fee_gwei": Web3.from_wei(median_tip, "gwei"),
        "max_fee_gwei": Web3.from_wei(max_fee, "gwei"),
    }

def get_network_congestion() -> str:
    """
    Classify current network congestion based on block gas utilization.
    Target = 15M gas (50% of 30M limit). Above = congested.
    """
    block = w3.eth.get_block("latest")
    utilization = block["gasUsed"] / block["gasLimit"]
    
    if utilization < 0.4:
        return "low"
    elif utilization < 0.6:
        return "normal"
    elif utilization < 0.8:
        return "high"
    else:
        return "very_high"

if __name__ == "__main__":
    congestion = get_network_congestion()
    print(f"Network congestion: {congestion.upper()}\n")
    for speed in SPEED_PROFILES:
        rec = get_gas_recommendation(speed)
        print(f"[{speed:8}] priority: {rec['priority_fee_gwei']:.3f} Gwei | max: {rec['max_fee_gwei']:.3f} Gwei")
