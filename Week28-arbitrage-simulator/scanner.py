from multi_hop_quote import simulate_path
from gas_calculator import estimate_gas_for_path, calculate_gas_cost_eth
from paths import TRIANGLES
from web3 import Web3

INPUT_AMOUNT_ETH = 1.0  # Paper trade with 1 ETH
INPUT_WEI = Web3.to_wei(INPUT_AMOUNT_ETH, "ether")

def scan_once():
    results = []
    for triangle in TRIANGLES:
        result = simulate_path(INPUT_WEI, triangle["path"])
        
        gas_units = estimate_gas_for_path(len(triangle["path"]))
        gas_cost_eth = calculate_gas_cost_eth(gas_units)
        
        amount_out_eth = float(Web3.from_wei(result["amount_out"], "ether"))
        gross_profit_eth = amount_out_eth - INPUT_AMOUNT_ETH
        net_profit_eth = gross_profit_eth - float(gas_cost_eth)
        
        results.append({
            "name": triangle["name"],
            "rate": result["rate"],
            "gross_profit_eth": float(gross_profit_eth),
            "gas_cost_eth": float(gas_cost_eth),
            "net_profit_eth": net_profit_eth,
            "profitable": net_profit_eth > 0,
        })
    
    return results

if __name__ == "__main__":
    for r in scan_once():
        status = "✅ PROFITABLE" if r["profitable"] else "❌ Not profitable"
        print(f"{status} | {r['name']} | Net: {r['net_profit_eth']:.6f} ETH | Rate: {r['rate']:.6f}")
