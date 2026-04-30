from keeper.config import config
from gas.gas_oracle import get_gas_recommendation

def is_profitable(opportunity) -> tuple[bool, str]:
    """
    Returns (is_profitable: bool, reason: str).
    Reason explains rejection for logging.
    """
    # Check minimum profit threshold
    if opportunity.net_profit_eth < config.min_profit_eth:
        return False, f"Net profit {opportunity.net_profit_eth:.6f} ETH below minimum {config.min_profit_eth}"

    # Check current gas price against our ceiling
    gas_rec = get_gas_recommendation("fast")
    current_base_gwei = gas_rec["base_fee_gwei"]
    if current_base_gwei > config.max_gas_gwei:
        return False, f"Base fee {current_base_gwei:.1f} Gwei exceeds maximum {config.max_gas_gwei}"

    # Check ROI floor (protect against very large, low-margin trades)
    roi = opportunity.net_profit_eth / max(opportunity.input_amount_eth, 1e-9)
    if roi < 0.001:   # minimum 0.1% ROI
        return False, f"ROI {roi*100:.4f}% below 0.1% floor"

    return True, "profitable"
