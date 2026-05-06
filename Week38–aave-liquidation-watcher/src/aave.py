from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider
from src.config import config

# Minimal ABI — only the two functions we need
POOL_ADDRESSES_PROVIDER_ABI = [
    {
        "inputs": [],
        "name": "getPool",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
]

POOL_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
        "name": "getUserAccountData",
        "outputs": [
            {"internalType": "uint256", "name": "totalCollateralBase", "type": "uint256"},
            {"internalType": "uint256", "name": "totalDebtBase", "type": "uint256"},
            {"internalType": "uint256", "name": "availableBorrowsBase", "type": "uint256"},
            {"internalType": "uint256", "name": "currentLiquidationThreshold", "type": "uint256"},
            {"internalType": "uint256", "name": "ltv", "type": "uint256"},
            {"internalType": "uint256", "name": "healthFactor", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    }
]

# Cached references — initialised once on first call
_w3: AsyncWeb3 | None = None
_pool_contract = None

WAD = 10 ** 18   # Aave health factor scale: 1e18 = health factor of 1.0
BASE = 10 ** 8   # Aave USD values scale: 1e8 = $1.00


async def _get_pool_contract():
    global _w3, _pool_contract

    if _pool_contract:
        return _pool_contract

    _w3 = AsyncWeb3(AsyncHTTPProvider(config.rpc_url))

    addresses_provider = _w3.eth.contract(
        address=AsyncWeb3.to_checksum_address(config.aave_pool_addresses_provider),
        abi=POOL_ADDRESSES_PROVIDER_ABI,
    )
    pool_address = await addresses_provider.functions.getPool().call()
    _pool_contract = _w3.eth.contract(
        address=pool_address,
        abi=POOL_ABI,
    )
    print(f"[Aave] Connected to Pool at {pool_address}")
    return _pool_contract


async def get_user_position(wallet_address: str) -> dict:
    """
    Fetch Aave V3 position data for a wallet.
    Returns human-readable values: health_factor as float, USD values as float.

    getUserAccountData returns:
      - collateral/debt/borrows in USD with 8 decimals (Base units)
      - health factor in WAD (18 decimals): 1e18 = HF of 1.0
      - ltv and liquidation_threshold in basis points (e.g. 8000 = 80%)
    """
    pool = await _get_pool_contract()
    checksum_address = AsyncWeb3.to_checksum_address(wallet_address)

    (
        total_collateral_base,
        total_debt_base,
        available_borrows_base,
        current_liquidation_threshold,
        ltv,
        health_factor_raw,
    ) = await pool.functions.getUserAccountData(checksum_address).call()

    # Health factor: uint256 max means no debt (infinite HF)
    if health_factor_raw >= (2**256 - 1) // 2:
        health_factor = float("inf")
    else:
        health_factor = health_factor_raw / WAD

    return {
        "health_factor":          health_factor,
        "total_collateral_usd":   total_collateral_base / BASE,
        "total_debt_usd":         total_debt_base / BASE,
        "available_borrows_usd":  available_borrows_base / BASE,
        "ltv":                    ltv / 100,                       # basis points → %
        "liquidation_threshold":  current_liquidation_threshold / 100,
    }


def simulate_liquidation(position: dict) -> dict | None:
    """
    Calculate what a liquidator could theoretically earn.
    SIMULATION ONLY — this bot never submits transactions.

    Aave rules:
      - Close factor: up to 50% of debt can be repaid in one liquidation
      - Liquidation bonus: ~5% extra collateral received (varies by asset)
    """
    if position["health_factor"] >= 1.0:
        return None

    CLOSE_FACTOR = 0.5
    LIQUIDATION_BONUS = 1.05  # 5% bonus

    debt_to_repay    = position["total_debt_usd"] * CLOSE_FACTOR
    collateral_gain  = debt_to_repay * LIQUIDATION_BONUS
    profit           = collateral_gain - debt_to_repay

    return {
        "debt_to_repay":   debt_to_repay,
        "collateral_gain": collateral_gain,
        "profit":          profit,
    }
