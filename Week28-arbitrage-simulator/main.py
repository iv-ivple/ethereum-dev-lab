# main.py

import time
from web3 import Web3
from scanner import scan_once
from paper_trader import log_opportunity, get_summary
from paths import TRIANGLES
from multi_hop_quote import simulate_path_with_slippage
from gas_calculator import estimate_gas_for_path, calculate_gas_cost_eth
from profit_engine import calculate_opportunity
import os
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

INPUT_WEI = Web3.to_wei(1, "ether")
SLIPPAGE_TOLERANCE = 0.005  # 0.5%
POLL_INTERVAL = 12  # seconds (roughly one Ethereum block)

print("🔍 Arbitrage simulator starting — paper mode only, no real trades")

while True:
    block = w3.eth.block_number
    print(f"\n--- Block {block} ---")

    for triangle in TRIANGLES:
        gas_units = estimate_gas_for_path(len(triangle["path"]))
        gas_cost_eth = float(calculate_gas_cost_eth(gas_units))

        result = simulate_path_with_slippage(INPUT_WEI, triangle["path"], SLIPPAGE_TOLERANCE)
        opp = calculate_opportunity(triangle["name"], INPUT_WEI, result, gas_cost_eth)

        log_opportunity(opp, block)

        if opp.profitable:
            print(f"  ✅ {opp.name}: +{opp.net_profit_eth:.6f} ETH (${opp.net_profit_usd:.2f})")
        else:
            print(f"  ❌ {opp.name}: {opp.net_profit_eth:.6f} ETH")

    summary = get_summary()
    print(f"  📊 Summary: {summary['profitable_opportunities']}/{summary['total_scans']} profitable | Hit rate: {summary['hit_rate_percent']:.1f}%")

    time.sleep(POLL_INTERVAL)

