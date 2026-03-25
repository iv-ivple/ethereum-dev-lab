# arb/profit_engine.py

from dataclasses import dataclass
from typing import Optional

ETH_PRICE_USD = 3000  # Hardcode for paper trading; later fetch from Chainlink/CoinGecko

@dataclass
class ArbitrageOpportunity:
    name: str
    input_eth: float
    gross_profit_eth: float
    gas_cost_eth: float
    slippage_cost_eth: float
    net_profit_eth: float
    net_profit_usd: float
    roi_percent: float
    profitable: bool
    hops: list

def calculate_opportunity(
    triangle_name: str,
    input_wei: int,
    simulation_result: Optional[dict],
    gas_cost_eth: float,
) -> ArbitrageOpportunity:
    from web3 import Web3

    if simulation_result is None:
        # Slippage exceeded
        return ArbitrageOpportunity(
            name=triangle_name,
            input_eth=Web3.from_wei(input_wei, "ether"),
            gross_profit_eth=0,
            gas_cost_eth=gas_cost_eth,
            slippage_cost_eth=0,
            net_profit_eth=-float(gas_cost_eth),
            net_profit_usd=-float(gas_cost_eth) * ETH_PRICE_USD,
            roi_percent=0,
            profitable=False,
            hops=[],
        )

    gross_profit_wei = simulation_result["amount_out"] - input_wei
    gross_profit_eth = float(Web3.from_wei(abs(gross_profit_wei), "ether"))
    if gross_profit_wei < 0:
        gross_profit_eth = -gross_profit_eth

    # Slippage cost: difference between no-fee rate and actual rate
    ideal_output = input_wei * simulation_result["rate"]
    slippage_cost_eth = 0  # Already baked into AMM formula; track separately if needed

    net_profit_eth = gross_profit_eth - gas_cost_eth
    net_profit_usd = net_profit_eth * ETH_PRICE_USD
    input_eth = float(Web3.from_wei(input_wei, "ether"))
    roi = (net_profit_eth / input_eth) * 100 if input_eth > 0 else 0

    return ArbitrageOpportunity(
        name=triangle_name,
        input_eth=input_eth,
        gross_profit_eth=gross_profit_eth,
        gas_cost_eth=gas_cost_eth,
        slippage_cost_eth=slippage_cost_eth,
        net_profit_eth=net_profit_eth,
        net_profit_usd=net_profit_usd,
        roi_percent=roi,
        profitable=net_profit_eth > 0,
        hops=simulation_result["hops"],
    )
