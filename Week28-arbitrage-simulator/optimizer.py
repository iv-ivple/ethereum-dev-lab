def find_optimal_input(path: list, min_wei: int, max_wei: int, steps: int = 50) -> dict:
    """Binary-search-style sweep to find the input amount that maximizes net profit."""
    from arb.multi_hop_quote import simulate_path
    from arb.gas_calculator import estimate_gas_for_path, calculate_gas_cost_eth
    from web3 import Web3

    gas_units = estimate_gas_for_path(len(path))
    gas_cost_eth = float(calculate_gas_cost_eth(gas_units))

    best = {"input_wei": 0, "net_profit_eth": float("-inf")}
    step_size = (max_wei - min_wei) // steps

    for i in range(steps):
        amount = min_wei + i * step_size
        result = simulate_path(amount, path)
        gross = float(Web3.from_wei(result["amount_out"] - amount, "ether"))
        net = gross - gas_cost_eth
        if net > best["net_profit_eth"]:
            best = {"input_wei": amount, "net_profit_eth": net, "rate": result["rate"]}

    return best
