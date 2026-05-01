"""
keeper/database/state_store.py
------------------------------
Helper layer between keeper_bot.py and the database.
All raw SQLAlchemy session work lives here — nothing else should import Session directly.

Public API
----------
  StateStore(database_url)              -> class instance (used by keeper_bot.py)
    .open_run()                         -> int (run_id)
    .save_opportunity(opp, status, run_id) -> int (opp_id)
    .update_opportunity_status(id, status, **kwargs) -> None
    .close_run(run_id, stop_reason, stats) -> None
    .get_stats_for_run(run_id)          -> dict

  Module-level functions also available for standalone use.
"""

from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from keeper.config import config
from keeper.database.models import Base, Opportunity, OpportunityStatus, KeeperRun

# ---------------------------------------------------------------------------
# Engine + session factory (one engine per process)
# ---------------------------------------------------------------------------

engine = create_engine(
    config.database_url,
    # For Postgres: keep a small connection pool, let SQLAlchemy recycle
    pool_pre_ping=True,   # drops stale connections before use
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_session() -> Session:
    """Return a new session. Callers are responsible for closing it."""
    return SessionLocal()


# ---------------------------------------------------------------------------
# Opportunity helpers
# ---------------------------------------------------------------------------

def save_opportunity(opp_data: dict) -> Opportunity:
    """
    Persist a newly detected opportunity and return the saved row.

    Expected keys in opp_data (mirrors Opportunity model fields):
        strategy, description, gross_profit_eth, gas_cost_eth,
        net_profit_eth, input_amount_eth
    Optional keys:
        status (defaults to DETECTED), block_number
    """
    session = get_session()
    try:
        opp = Opportunity(
            strategy         = opp_data["strategy"],
            description      = opp_data["description"],
            gross_profit_eth = opp_data["gross_profit_eth"],
            gas_cost_eth     = opp_data["gas_cost_eth"],
            net_profit_eth   = opp_data["net_profit_eth"],
            input_amount_eth = opp_data["input_amount_eth"],
            status           = opp_data.get("status", OpportunityStatus.DETECTED),
            block_number     = opp_data.get("block_number"),
        )
        session.add(opp)
        session.commit()
        session.refresh(opp)
        return opp
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def update_opportunity_status(
    opportunity_id: int,
    status: OpportunityStatus,
    *,
    tx_hash: str | None = None,
    gas_used: int | None = None,
    error_message: str | None = None,
    confirmed_at: datetime | None = None,
) -> None:
    """
    Update the status (and optional fields) of an existing opportunity row.

    Called by the executor as the tx progresses through states:
        EXECUTING → SUCCESS / REVERTED / TIMEOUT / SKIPPED
    """
    session = get_session()
    try:
        opp = session.get(Opportunity, opportunity_id)
        if opp is None:
            raise ValueError(f"Opportunity {opportunity_id} not found")

        opp.status = status

        if tx_hash is not None:
            opp.tx_hash = tx_hash
        if gas_used is not None:
            opp.gas_used = gas_used
        if error_message is not None:
            opp.error_message = error_message
        if confirmed_at is not None:
            opp.confirmed_at = confirmed_at
        elif status == OpportunityStatus.SUCCESS:
            # Auto-stamp confirmation time when marking as success
            opp.confirmed_at = datetime.now(timezone.utc)

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Run helpers
# ---------------------------------------------------------------------------

def open_run() -> KeeperRun:
    """
    Insert a new KeeperRun row at bot startup and return it.
    Call this once at the start of KeeperBot.run().
    """
    session = get_session()
    try:
        run = KeeperRun(started_at=datetime.now(timezone.utc))
        session.add(run)
        session.commit()
        session.refresh(run)
        return run
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def close_run(run_id: int, stop_reason: str, stats: dict) -> None:
    """
    Stamp the KeeperRun row with final counters when the bot shuts down.

    stats dict keys (all optional — missing keys are left at their DB defaults):
        blocks_scanned, opportunities_found, txs_success, txs_failed,
        total_profit_eth
    """
    session = get_session()
    try:
        run = session.get(KeeperRun, run_id)
        if run is None:
            raise ValueError(f"KeeperRun {run_id} not found")

        run.stopped_at           = datetime.now(timezone.utc)
        run.stop_reason          = stop_reason
        run.blocks_scanned       = stats.get("blocks_scanned",       run.blocks_scanned)
        run.opportunities_found  = stats.get("opportunities_found",  run.opportunities_found)
        run.txs_success          = stats.get("txs_success",          run.txs_success)
        run.txs_failed           = stats.get("txs_failed",           run.txs_failed)
        run.total_profit_eth     = stats.get("total_profit_eth",     run.total_profit_eth)

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Stats query
# ---------------------------------------------------------------------------

def get_stats_for_run(run_id: int) -> dict:
    """
    Return a summary dict for a completed (or in-progress) run.

    Aggregates opportunity outcomes directly from the opportunities table
    so the numbers are always source-of-truth even if the run row wasn't
    closed cleanly (e.g. after a crash).
    """
    from sqlalchemy import func, select

    session = get_session()
    try:
        # Pull the run row itself
        run = session.get(KeeperRun, run_id)
        if run is None:
            raise ValueError(f"KeeperRun {run_id} not found")

        # Aggregate opportunity outcomes for this run's time window
        # (opportunities don't store run_id directly, so we approximate
        #  by filtering on detected_at between run start and stop/now)
        stop = run.stopped_at or datetime.now(timezone.utc)

        counts_q = (
            select(
                Opportunity.status,
                func.count(Opportunity.id).label("n"),
                func.sum(Opportunity.net_profit_eth).label("profit"),
            )
            .where(Opportunity.detected_at >= run.started_at)
            .where(Opportunity.detected_at <= stop)
            .group_by(Opportunity.status)
        )
        rows = session.execute(counts_q).all()

        by_status = {row.status: {"count": row.n, "profit": row.profit or 0.0} for row in rows}

        return {
            "run_id":               run.id,
            "started_at":           run.started_at,
            "stopped_at":           run.stopped_at,
            "stop_reason":          run.stop_reason,
            "blocks_scanned":       run.blocks_scanned,
            "opportunities_found":  run.opportunities_found,
            "txs_success":          by_status.get(OpportunityStatus.SUCCESS,  {}).get("count",  0),
            "txs_reverted":         by_status.get(OpportunityStatus.REVERTED, {}).get("count",  0),
            "txs_timeout":          by_status.get(OpportunityStatus.TIMEOUT,  {}).get("count",  0),
            "txs_skipped":          by_status.get(OpportunityStatus.SKIPPED,  {}).get("count",  0),
            "total_profit_eth":     by_status.get(OpportunityStatus.SUCCESS,  {}).get("profit", 0.0),
        }
    finally:
        session.close()


# ---------------------------------------------------------------------------
# StateStore class — used by keeper_bot.py as self.db = StateStore(url)
# ---------------------------------------------------------------------------

class StateStore:
    """
    Thin class wrapper around the module-level functions.
    keeper_bot.py uses this as: self.db = StateStore(config.database_url)

    Accepts database_url so it can create its own engine — easy to mock
    in tests and swap URLs per environment.
    """

    def __init__(self, database_url: str):
        self._engine = create_engine(
            database_url,
            pool_pre_ping=True,
            future=True,
        )
        self._Session = sessionmaker(bind=self._engine, autocommit=False, autoflush=False)

    def _get_session(self):
        return self._Session()

    def open_run(self) -> int:
        """Insert a new KeeperRun row and return its id."""
        session = self._get_session()
        try:
            run = KeeperRun(started_at=datetime.now(timezone.utc))
            session.add(run)
            session.commit()
            session.refresh(run)
            return run.id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def save_opportunity(self, opp, status: str = "detected", run_id: int = None) -> int:
        """
        Persist an opportunity dataclass/object and return its DB id.
        Accepts either a dict or an object with matching attributes.
        """
        session = self._get_session()
        try:
            db_opp = Opportunity(
                strategy         = opp.strategy,
                description      = opp.description,
                gross_profit_eth = opp.gross_profit_eth,
                gas_cost_eth     = opp.gas_cost_eth,
                net_profit_eth   = opp.net_profit_eth,
                input_amount_eth = opp.input_amount_eth,
                status           = OpportunityStatus(status) if isinstance(status, str) else status,
            )
            session.add(db_opp)
            session.commit()
            session.refresh(db_opp)
            return db_opp.id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_opportunity_status(
        self,
        opportunity_id: int,
        status: str,
        *,
        tx_hash: str | None = None,
        gas_used: int | None = None,
        error_message: str | None = None,
    ) -> None:
        session = self._get_session()
        try:
            opp = session.get(Opportunity, opportunity_id)
            if opp is None:
                raise ValueError(f"Opportunity {opportunity_id} not found")
            opp.status = OpportunityStatus(status) if isinstance(status, str) else status
            if tx_hash is not None:
                opp.tx_hash = tx_hash
            if gas_used is not None:
                opp.gas_used = gas_used
            if error_message is not None:
                opp.error_message = error_message
            if status == "success":
                opp.confirmed_at = datetime.now(timezone.utc)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close_run(self, run_id: int, stop_reason: str, stats: dict) -> None:
        session = self._get_session()
        try:
            run = session.get(KeeperRun, run_id)
            if run is None:
                raise ValueError(f"KeeperRun {run_id} not found")
            run.stopped_at          = datetime.now(timezone.utc)
            run.stop_reason         = stop_reason
            run.blocks_scanned      = stats.get("blocks",        run.blocks_scanned)
            run.opportunities_found = stats.get("opportunities", run.opportunities_found)
            run.txs_success         = stats.get("success",       run.txs_success)
            run.txs_failed          = stats.get("failed",        run.txs_failed)
            run.total_profit_eth    = stats.get("profit",        run.total_profit_eth)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_stats_for_run(self, run_id: int) -> dict:
        return get_stats_for_run(run_id)
