import asyncio
import logging
import signal
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.config import config
from src.db import init_db, close_db, get_active_wallets
from src.watcher import run_poll_cycle, seed_wallets, get_snapshots_saved
from src.notifier import send_heartbeat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("🚀 Aave Liquidation Watcher starting...")
    logger.info(f"   Warning threshold:  HF < {config.health_factor_warning}")
    logger.info(f"   Critical threshold: HF < {config.health_factor_critical}")
    logger.info(f"   Poll interval:      {config.poll_interval_seconds}s")

    # Initialise database pool
    await init_db()

    # Seed wallets from .env (safe to run every startup — upsert is idempotent)
    await seed_wallets()

    # Run one poll cycle immediately on startup
    await run_poll_cycle()

    # Set up APScheduler for recurring polls
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        run_poll_cycle,
        trigger="interval",
        seconds=config.poll_interval_seconds,
        id="poll_cycle",
    )

    # Hourly heartbeat so you know the bot is alive in Discord
    scheduler.add_job(
        _send_heartbeat_job,
        trigger="cron",
        minute=0,
        id="heartbeat",
    )

    scheduler.start()
    logger.info("✅ Watcher running. Press Ctrl+C to stop.")

    # Keep the event loop alive until a shutdown signal
    stop_event = asyncio.Event()

    def _handle_signal():
        logger.info("\n[Watcher] Shutdown signal received...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handle_signal)

    await stop_event.wait()

    # Graceful shutdown
    scheduler.shutdown(wait=False)
    await close_db()
    logger.info("[DB] Connection pool closed. Goodbye.")


async def _send_heartbeat_job():
    wallets = await get_active_wallets()
    await send_heartbeat(
        wallets_count=len(wallets),
        snapshots_saved=get_snapshots_saved(),
    )


if __name__ == "__main__":
    asyncio.run(main())
