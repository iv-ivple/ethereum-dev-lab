import asyncio
import logging
from src.aave import get_user_position, simulate_liquidation
from src.db import get_active_wallets, save_snapshot, record_alert, upsert_wallet
from src.notifier import send_alert
from src.config import config

logger = logging.getLogger(__name__)

# Simple in-process counter for the heartbeat message
snapshots_saved = 0


async def _with_retry(coro_fn, retries: int = 3, delay: float = 2.0):
    """Retry an async function up to `retries` times with a fixed delay."""
    for attempt in range(retries):
        try:
            return await coro_fn()
        except Exception as exc:
            if attempt == retries - 1:
                raise
            logger.warning(f"Attempt {attempt + 1} failed: {exc}. Retrying in {delay}s...")
            await asyncio.sleep(delay)


async def _process_wallet(wallet: dict) -> None:
    global snapshots_saved
    address = wallet["address"]

    # 1. Fetch position from Aave (with retry)
    try:
        position = await _with_retry(lambda: get_user_position(address))
    except Exception as exc:
        logger.error(f"[Watcher] Could not fetch position for {address}: {exc}")
        return

    hf = position["health_factor"]
    hf_display = "∞" if hf == float("inf") else f"{hf:.4f}"
    logger.info(
        f"[Watcher] {address} | HF: {hf_display} | "
        f"Debt: ${position['total_debt_usd']:.2f}"
    )

    # 2. Save snapshot regardless of health status
    try:
        await save_snapshot(wallet["id"], position)
        snapshots_saved += 1
    except Exception as exc:
        logger.error(f"[DB] Failed to save snapshot for {address}: {exc}")

    # 3. Skip alert logic if no debt (health factor is infinite)
    if position["total_debt_usd"] == 0:
        return

    # 4. Determine alert level
    alert_type = None
    if hf < config.health_factor_critical:
        alert_type = "CRITICAL"
    elif hf < config.health_factor_warning:
        alert_type = "WARNING"

    if not alert_type:
        return

    # 5. Dedup: only alert once per type per hour (enforced at DB level)
    is_new = await record_alert(
        wallet["id"], alert_type, hf, f"HF dropped to {hf:.4f}"
    )
    if not is_new:
        logger.info(f"[Watcher] Alert already sent this hour for {address} ({alert_type})")
        return

    # 6. Simulate liquidation opportunity if already liquidatable
    simulation = simulate_liquidation(position) if hf < 1.0 else None

    # 7. Send Discord alert
    try:
        await send_alert(
            alert_type=alert_type,
            wallet_address=address,
            position=position,
            simulation=simulation,
        )
        logger.info(f"[Discord] Sent {alert_type} alert for {address}")
    except Exception as exc:
        logger.error(f"[Discord] Failed to send alert: {exc}")


async def run_poll_cycle() -> None:
    """Fetch and process all active wallets. Called on a schedule."""
    wallets = await get_active_wallets()
    logger.info(f"\n[Watcher] Poll cycle — {len(wallets)} wallet(s) | starting now")

    for wallet in wallets:
        await _process_wallet(wallet)
        await asyncio.sleep(0.5)  # Small delay between wallets to avoid RPC rate limits


async def seed_wallets() -> None:
    """Insert wallets from .env into the DB on first run (idempotent)."""
    for address in config.seed_wallets:
        wallet = await upsert_wallet(address)
        logger.info(f"[DB] Seeded wallet: {wallet['address']}")


def get_snapshots_saved() -> int:
    return snapshots_saved
