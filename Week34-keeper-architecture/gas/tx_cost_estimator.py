# gas/tx_cost_estimator.py
from web3 import Web3
from gas.gas_oracle import get_gas_recommendation
import requests
import os
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

def get_eth_price_usd() -> float:
    """Fetch ETH/USD price from Coingecko public API (no key needed)."""
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "ethereum", "vs_currencies": "usd"},
            timeout=5,
        )
        return r.json()["ethereum"]["usd"]
    except Exception:
        return None

def estimate_tx_cost(tx: dict, speed: str = "standard") -> dict:
    """
    Full cost estimate for a transaction at a given speed.
    tx: partial tx dict with at least 'from', 'to', and optionally 'data'
    """
    gas_units = w3.eth.estimate_gas(tx)
    fees = get_gas_recommendation(speed)
    
    cost_wei = gas_units * fees["max_fee_per_gas"]
    cost_eth = float(Web3.from_wei(cost_wei, "ether"))
    
    eth_price = get_eth_price_usd()
    cost_usd = cost_eth * eth_price if eth_price else None
    
    return {
        "gas_units": gas_units,
        "max_fee_per_gas_gwei": fees["max_fee_gwei"],
        "priority_fee_gwei": fees["priority_fee_gwei"],
        "cost_eth": cost_eth,
        "cost_usd": cost_usd,
        "speed": speed,
    }
