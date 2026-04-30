async def subscribe_to_event(w3, contract_address: str, event_abi: dict, on_event):
    """
    Polls eth_getLogs for a specific event on each new block.
    Use this for strategies triggered by contract events (liquidation thresholds,
    price updates, collateral changes).
    """
    contract = w3.eth.contract(address=contract_address, abi=[event_abi])
    last_block = await w3.eth.block_number

    async def handle_new_block(block_number: int):
        nonlocal last_block
        events = await contract.events[event_abi["name"]].get_logs(
            fromBlock=last_block + 1, toBlock=block_number
        )
        for event in events:
            await on_event(event)
        last_block = block_number

    return handle_new_block
