#!/usr/bin/env python3
"""
Estimate gas costs for Ethereum transactions.
Compare different gas prices and calculate transaction costs.
"""

from web3 import Web3
from dotenv import load_dotenv
import os

load_dotenv()

def estimate_simple_transfer(w3):
    """Estimate gas for a simple ETH transfer."""
    return 21000  # Fixed cost for simple ETH transfer

def get_gas_prices(w3):
    """Get current gas prices at different priority levels."""
    current_gas = w3.eth.gas_price
    current_gwei = float(w3.from_wei(current_gas, 'gwei'))
    
    return {
        'slow': current_gwei * 0.8,      # 20% below average
        'average': current_gwei,
        'fast': current_gwei * 1.2,      # 20% above average
        'instant': current_gwei * 1.5    # 50% above average
    }

def calculate_cost(gas_limit, gas_price_gwei, eth_price_usd=None):
    """Calculate transaction cost in ETH and USD."""
    gas_price_wei = Web3.to_wei(gas_price_gwei, 'gwei')
    total_wei = gas_limit * gas_price_wei
    total_eth = Web3.from_wei(total_wei, 'ether')
    
    result = {
        'gas_limit': gas_limit,
        'gas_price_gwei': gas_price_gwei,
        'total_eth': float(total_eth)
    }
    
    if eth_price_usd:
        result['total_usd'] = float(total_eth) * eth_price_usd
    
    return result

def main():
    print("=" * 70)
    print("GAS PRICE ESTIMATOR")
    print("=" * 70)
    print()
    
      # Connect to Ethereum (read-only for nonce and gas price)
    rpc_url = os.getenv('RPC_URL', 'https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY')
    w3 = Web3(Web3.HTTPProvider(rpc_url))

    
    if not w3.is_connected():
        print("❌ Failed to connect to Ethereum node")
        return
    
    print("✅ Connected to Ethereum Mainnet")
    print()
    
    # Get current gas prices
    gas_prices = get_gas_prices(w3)
    
    print("⛽ Current Gas Prices (Gwei):")
    print(f"   Slow:    {gas_prices['slow']:.2f} Gwei (~10+ min)")
    print(f"   Average: {gas_prices['average']:.2f} Gwei (~3-5 min)")
    print(f"   Fast:    {gas_prices['fast']:.2f} Gwei (~1-2 min)")
    print(f"   Instant: {gas_prices['instant']:.2f} Gwei (~30 sec)")
    print()
    
    # Estimate costs for simple transfer
    gas_limit = estimate_simple_transfer(w3)
    eth_price = 2000  # Example ETH price in USD
    
    print(f"💸 Cost Estimates for Simple ETH Transfer ({gas_limit} gas):")
    print(f"   (Assuming ETH = ${eth_price})")
    print("-" * 70)
    
    for speed, gas_price in gas_prices.items():
        cost = calculate_cost(gas_limit, gas_price, eth_price)
        print(f"\n   {speed.capitalize():8} | "
              f"{cost['gas_price_gwei']:8.2f} Gwei | "
              f"{cost['total_eth']:.6f} ETH | "
              f"${cost['total_usd']:.2f} USD")
    
    print()
    print("=" * 70)
    print("💡 Gas Optimization Tips:")
    print("  • Simple transfers: Always 21,000 gas")
    print("  • Smart contract calls: Varies, use eth_estimateGas")
    print("  • Batch transactions to save gas")
    print("  • Use Layer 2 solutions for cheaper transactions")
    print("  • Check gas prices at ethgasstation.info or etherscan.io")
    print("=" * 70)

if __name__ == "__main__":
    main()
