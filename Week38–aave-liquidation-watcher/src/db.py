import asyncpg
import math
from src.config import config

# Module-level connection pool, initialised once in main.py
_pool: asyncpg.Pool | None = None


async def init_db():
    """Call once at startup to create the connection pool."""
    global _pool
    _pool = await asyncpg.create_pool(config.database_url, min_size=2, max_size=10)


async def close_db():
    """Call on shutdown to cleanly close all connections."""
    if _pool:
        await _pool.close()


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool not initialised. Call init_db() first.")
    return _pool


# ── Wallets ───────────────────────────────────────────────────────────────────

async def upsert_wallet(address: str, label: str | None = None) -> dict:
    row = await get_pool().fetchrow(
        """
        INSERT INTO wallets (address, label)
        VALUES ($1, $2)
        ON CONFLICT (address)
        DO UPDATE SET label = COALESCE($2, wallets.label)
        RETURNING *
        """,
        address.lower(), label,
    )
    return dict(row)


async def get_active_wallets() -> list[dict]:
    rows = await get_pool().fetch(
        "SELECT * FROM wallets WHERE active = TRUE ORDER BY added_at"
    )
    return [dict(r) for r in rows]


# ── Position Snapshots ────────────────────────────────────────────────────────

async def save_snapshot(wallet_id: int, position: dict) -> dict:
    row = await get_pool().fetchrow(
        """
        INSERT INTO position_snapshots
            (wallet_id, health_factor, total_collateral_usd, total_debt_usd,
             available_borrows_usd, ltv, liquidation_threshold)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
        """,
        wallet_id,
        999999 if math.isinf(position["health_factor"]) else position["health_factor"],
        position["total_collateral_usd"],
        position["total_debt_usd"],
        position["available_borrows_usd"],
        position["ltv"],
        position["liquidation_threshold"],
    )
    return dict(row)


async def get_recent_snapshots(wallet_id: int, hours: int = 24) -> list[dict]:
    rows = await get_pool().fetch(
        """
        SELECT * FROM position_snapshots
        WHERE wallet_id = $1
          AND recorded_at >= NOW() - ($2 || ' hours')::INTERVAL
        ORDER BY recorded_at DESC
        """,
        wallet_id, str(hours),
    )
    return [dict(r) for r in rows]


# ── Alerts ────────────────────────────────────────────────────────────────────

async def record_alert(
    wallet_id: int,
    alert_type: str,
    health_factor: float,
    message: str,
) -> bool:
    """
    Insert an alert. Returns True if inserted (new alert), False if it's a
    duplicate within the current hour (unique index violation).
    """
    try:
        await get_pool().execute(
            """
            INSERT INTO alerts (wallet_id, alert_type, health_factor, message)
            VALUES ($1, $2, $3, $4)
            """,
            wallet_id, alert_type, health_factor, message,
        )
        return True
    except asyncpg.UniqueViolationError:
        return False  # Already alerted this hour — suppress duplicate
