# arb/multi_hop_quote.py

from web3 import Web3
import os
from dotenv import load_dotenv
from config import TOKENS, MONITORED_PAIRS


load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

PAIR_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"name": "_reserve0", "type": "uint112"},
            {"name": "_reserve1", "type": "uint112"},
            {"name": "_blockTimestampLast", "type": "uint32"},
        ],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token0",
        "outputs": [{"name": "", "type": "address"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token1",
        "outputs": [{"name": "", "type": "address"}],
        "type": "function",
    },
]

def get_amount_out(amount_in: int, reserve_in: int, reserve_out: int) -> int:
    """Uniswap V2 exact-in formula with 0.3% fee."""
    amount_in_with_fee = amount_in * 997
    numerator = amount_in_with_fee * reserve_out
    denominator = (reserve_in * 1000) + amount_in_with_fee
    return numerator // denominator

def simulate_path(amount_in: int, path: list[dict]) -> dict:
    """
    path: list of {"pair": "0x...", "token_in": "0x..."}
    Returns: {"amount_out": int, "hops": [...], "rate": float}
    """
    current_amount = amount_in
    hops = []

    for step in path:
        pair = w3.eth.contract(
            address=Web3.to_checksum_address(step["pair"]),
            abi=PAIR_ABI
        )
        reserves = pair.functions.getReserves().call()
        token0 = pair.functions.token0().call()

        if step["token_in"].lower() == token0.lower():
            reserve_in, reserve_out = reserves[0], reserves[1]
        else:
            reserve_in, reserve_out = reserves[1], reserves[0]

        amount_out = get_amount_out(current_amount, reserve_in, reserve_out)
        hops.append({
            "pair": step["pair"],
            "amount_in": current_amount,
            "amount_out": amount_out,
            "reserve_in": reserve_in,
            "reserve_out": reserve_out,
        })
        current_amount = amount_out

    return {
        "amount_out": current_amount,
        "hops": hops,
        "rate": current_amount / amount_in,
    }

def calculate_price_impact(amount_in: int, reserve_in: int, reserve_out: int) -> float:
    """
    Price impact as a percentage: how much worse is execution vs. mid-price.
    Mid-price = reserve_out / reserve_in
    """
    mid_price = reserve_out / reserve_in
    amount_out = get_amount_out(amount_in, reserve_in, reserve_out)
    execution_price = amount_out / amount_in
    impact = (mid_price - execution_price) / mid_price
    return impact * 100  # as percentage

def simulate_path_with_slippage(amount_in: int, path: list, slippage_tolerance: float = 0.005):
    """
    slippage_tolerance: e.g. 0.005 = 0.5%
    Returns None if any hop exceeds tolerance.
    """
    result = simulate_path(amount_in, path)
    for hop in result["hops"]:
        impact = calculate_price_impact(
            hop["amount_in"], hop["reserve_in"], hop["reserve_out"]
        )
        if impact / 100 > slippage_tolerance:
            return None  # Abort — too much slippage on this hop
    return result



if __name__ == "__main__":
    ONE_WETH = 10**18

    # ── Triangle: WETH → USDC (Uni) → DAI (Sushi) → WETH (Uni) ──────────────
    triangle = [
        {
            "pair": MONITORED_PAIRS["WETH/USDC"]["uniswap"],
            "token_in": TOKENS["WETH"],
        },
        {
            "pair": MONITORED_PAIRS["USDC/DAI"]["sushiswap"],
            "token_in": TOKENS["USDC"],
        },
        {
            "pair": MONITORED_PAIRS["WETH/DAI"]["uniswap"],
            "token_in": TOKENS["DAI"],
        },
    ]

    result = simulate_path(ONE_WETH, triangle)

    print(f"Amount in:  {ONE_WETH / 1e18:.6f} WETH")
    print(f"Amount out: {result['amount_out'] / 1e18:.6f} WETH")
    print(f"Rate:       {result['rate']:.8f}  (1.0 = break-even)")
    print(f"P&L:        {(result['rate'] - 1) * 100:.4f}%")
    print()
    for i, hop in enumerate(result["hops"]):
        print(f"Hop {i+1}: {hop['amount_in']} → {hop['amount_out']}")
        print(f"       pair={hop['pair']}")
