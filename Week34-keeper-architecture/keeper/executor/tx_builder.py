from web3 import Web3
from keeper.config import config
from gas.gas_oracle import get_gas_recommendation

def build_tx(opportunity, w3: Web3, nonce: int) -> dict:
    """
    Build an EIP-1559 transaction dict from an Opportunity.
    The actual `to`, `data`, and `value` fields depend on the strategy.
    """
    gas_rec = get_gas_recommendation("fast")

    # Strategy-specific calldata generation
    if opportunity.strategy == "arb_triangle":
        to, data, value = build_arb_calldata(opportunity.metadata, w3)
    else:
        raise ValueError(f"Unknown strategy: {opportunity.strategy}")

    return {
        "from":                 config.keeper_address,
        "to":                   to,
        "data":                 data,
        "value":                value,
        "nonce":                nonce,
        "gas":                  400_000,     # conservative; replaced with estimate below
        "maxFeePerGas":         gas_rec["max_fee_wei"],
        "maxPriorityFeePerGas": gas_rec["priority_fee_wei"],
        "chainId":              1,
    }

def build_arb_calldata(metadata: dict, w3: Web3):
    """
    Encode the swap path into calldata for your flash-arb contract
    (or use Uniswap Router directly for simple paths).
    """
    # Placeholder — implement per your contract interface
    raise NotImplementedError("Implement calldata encoding for your arb contract")
