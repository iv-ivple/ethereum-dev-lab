# competition_model.py

def estimate_competition_cost(
    net_profit_eth: float,
    num_competitors: int = 10,
    bid_fraction: float = 0.90,
) -> dict:
    """
    In a Priority Gas Auction, bots bid up to ~90% of the profit as priority fee.
    Model the realistic take-home after competition.
    """
    max_bid = net_profit_eth * bid_fraction
    your_realistic_take = net_profit_eth - max_bid  # what's left after bidding

    return {
        "gross_profit_eth": net_profit_eth,
        "max_priority_bid_eth": max_bid,
        "realistic_take_eth": your_realistic_take,
        "viable": your_realistic_take > 0,
        "note": f"With {num_competitors} bots competing, you'd bid ~{bid_fraction*100:.0f}% of profit as priority fee"
    }
