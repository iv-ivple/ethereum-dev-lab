"""
tests/integration/test_keeper_pipeline.py
------------------------------------------
Integration tests for the full KeeperBot pipeline.
No real RPC, no real DB, no real Telegram — everything is mocked.

Scenarios:
  1. Happy path: scan → profitable → tx submitted → confirmed → stats updated → alert sent
  2. Below min profit: scan → not profitable → logged as skipped → IDLE
  3. Transaction revert: executor raises → failure counter increments → cooldown → IDLE
  4. Max failures: 5 consecutive failures → SHUTTING_DOWN → close_run() called

Run with:
    pytest tests/integration/test_keeper_pipeline.py -v
"""

import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Minimal stand-ins so we don't need the full keeper package installed
# ---------------------------------------------------------------------------

@dataclass
class FakeOpportunity:
    strategy: str = "arb_triangle"
    description: str = "WETH→USDC→DAI→WETH"
    gross_profit_eth: float = 0.01
    gas_cost_eth: float = 0.003
    net_profit_eth: float = 0.007
    input_amount_eth: float = 1.0
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {"path": ["WETH", "USDC", "DAI", "WETH"]}


FAKE_RECEIPT = {
    "transactionHash": bytes.fromhex("abcd" * 16),
    "status": 1,
    "gasUsed": 150000,
}

BLOCK_NUMBER = 19_000_000


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def bot():
    """
    Build a KeeperBot with ALL external dependencies mocked out.
    Patches are applied before __init__ so no real connections are attempted.
    """
    # We patch at the keeper_bot module level so the bot picks up the mocks
    with (
        patch("keeper_bot.config") as mock_cfg,
        patch("keeper_bot.Web3") as mock_web3_cls,
        patch("keeper_bot.ArbStrategy") as mock_strategy_cls,
        patch("keeper_bot.StateStore") as mock_store_cls,
        patch("keeper_bot.send_alert", new_callable=AsyncMock) as mock_alert,
        patch("keeper_bot.is_profitable") as mock_profitable,
        patch("keeper_bot.build_tx") as mock_build,
        patch("keeper_bot.sign_tx") as mock_sign,
        patch("keeper_bot.submit_and_confirm", new_callable=AsyncMock) as mock_submit,
        patch("keeper_bot.BlockListener") as mock_listener_cls,
        patch("keeper_bot.asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        # Config
        mock_cfg.validate.return_value = None
        mock_cfg.rpc_http_url = "https://fake-rpc.example.com"
        mock_cfg.rpc_ws_url = "wss://fake-rpc.example.com"
        mock_cfg.keeper_address = "0xDeadBeef00000000000000000000000000000001"
        mock_cfg.min_profit_eth = 0.002
        mock_cfg.max_gas_gwei = 50.0
        mock_cfg.max_consecutive_failures = 5
        mock_cfg.cooldown_seconds = 0        # no real sleeping in tests
        mock_cfg.tx_confirm_timeout_blocks = 3
        mock_cfg.database_url = "sqlite:///:memory:"

        # Web3
        mock_w3 = MagicMock()
        mock_w3.eth.get_transaction_count.return_value = 42
        mock_web3_cls.return_value = mock_w3
        mock_web3_cls.HTTPProvider = MagicMock()

        # Strategy
        mock_strategy = AsyncMock()
        mock_strategy_cls.return_value = mock_strategy

        # DB / StateStore
        mock_db = MagicMock()
        mock_db.open_run.return_value = 1
        mock_db.save_opportunity.return_value = 99   # fake opp_id
        mock_store_cls.return_value = mock_db

        # tx pipeline defaults (overridden per-test)
        mock_build.return_value = {"data": "0x..."}
        mock_sign.return_value = b"raw_signed_tx"
        mock_submit.return_value = FAKE_RECEIPT

        # Default: profitable
        mock_profitable.return_value = (True, "profitable")

        from keeper_bot import KeeperBot
        from keeper.state_machine import KeeperState

        bot = KeeperBot()

        # Attach mocks to bot for easy assertion in tests
        bot._mock_strategy = mock_strategy
        bot._mock_db = mock_db
        bot._mock_alert = mock_alert
        bot._mock_profitable = mock_profitable
        bot._mock_submit = mock_submit
        bot._mock_sleep = mock_sleep
        bot._KeeperState = KeeperState

        yield bot


# ---------------------------------------------------------------------------
# Scenario 1 — Happy path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_happy_path(bot):
    """
    Scanner returns an opportunity → profitability check passes →
    tx submitted → confirmed → stats updated → alert sent → IDLE.
    """
    opp = FakeOpportunity()
    bot._mock_strategy.scan = AsyncMock(return_value=opp)
    bot._mock_profitable.return_value = (True, "profitable")
    bot._mock_submit.return_value = FAKE_RECEIPT

    await bot.on_new_block(BLOCK_NUMBER)

    # State machine ended at IDLE
    assert bot.state == bot._KeeperState.IDLE

    # Stats updated
    assert bot.stats["blocks"] == 1
    assert bot.stats["opportunities"] == 1
    assert bot.stats["success"] == 1
    assert bot.stats["failed"] == 0
    assert bot.stats["profit"] == pytest.approx(opp.net_profit_eth)

    # DB: opportunity saved twice (executing, then success update)
    bot._mock_db.save_opportunity.assert_called_once()
    bot._mock_db.update_opportunity_status.assert_called_once_with(
        99, "success", tx_hash=FAKE_RECEIPT["transactionHash"].hex()
    )

    # Alert sent with success message
    alert_calls = [str(c) for c in bot._mock_alert.call_args_list]
    assert any("✅" in c for c in alert_calls), "Expected success alert"

    # No failures
    assert bot.consecutive_failures == 0


# ---------------------------------------------------------------------------
# Scenario 2 — Below minimum profit
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_below_min_profit(bot):
    """
    Scanner returns an opportunity → profitability check fails →
    opportunity logged as skipped → state returns to IDLE.
    """
    opp = FakeOpportunity(net_profit_eth=0.0001)   # below min
    bot._mock_strategy.scan = AsyncMock(return_value=opp)
    bot._mock_profitable.return_value = (False, "Net profit 0.000100 ETH below minimum 0.002")

    await bot.on_new_block(BLOCK_NUMBER)

    # Ended at IDLE
    assert bot.state == bot._KeeperState.IDLE

    # Opportunity counted as found but not as success
    assert bot.stats["opportunities"] == 1
    assert bot.stats["success"] == 0
    assert bot.stats["profit"] == pytest.approx(0.0)

    # Saved to DB as skipped
    bot._mock_db.save_opportunity.assert_called_once_with(
        opp, status="skipped", run_id=bot.run_id
    )

    # tx pipeline never touched
    bot._mock_submit.assert_not_called()

    # No failure counted
    assert bot.consecutive_failures == 0


# ---------------------------------------------------------------------------
# Scenario 3 — Transaction revert
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_transaction_revert(bot):
    """
    Executor raises RuntimeError → failure counter increments →
    cooldown entered → IDLE after cooldown.
    """
    opp = FakeOpportunity()
    bot._mock_strategy.scan = AsyncMock(return_value=opp)
    bot._mock_profitable.return_value = (True, "profitable")
    bot._mock_submit.side_effect = RuntimeError("transaction reverted")

    await bot.on_new_block(BLOCK_NUMBER)

    # Failure recorded
    assert bot.stats["failed"] == 1
    assert bot.consecutive_failures == 1

    # Went through cooldown and back to IDLE (not SHUTTING_DOWN)
    assert bot.state == bot._KeeperState.IDLE

    # Cooldown sleep was called
    bot._mock_sleep.assert_called_once_with(bot._mock_sleep.call_args[0][0])

    # Error alert sent
    alert_calls = [str(c) for c in bot._mock_alert.call_args_list]
    assert any("❌" in c for c in alert_calls), "Expected failure alert"

    # close_run never called — bot is still running
    bot._mock_db.close_run.assert_not_called()


# ---------------------------------------------------------------------------
# Scenario 4 — Max failures reached
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_max_failures_triggers_shutdown(bot):
    """
    5 consecutive failures → SHUTTING_DOWN state → close_run() called.
    """
    opp = FakeOpportunity()
    bot._mock_strategy.scan = AsyncMock(return_value=opp)
    bot._mock_profitable.return_value = (True, "profitable")
    bot._mock_submit.side_effect = RuntimeError("node timeout")

    # Fire 5 blocks — each one fails
    for block in range(BLOCK_NUMBER, BLOCK_NUMBER + 5):
        await bot.on_new_block(block)

    # After 5 failures the bot should have shut down
    assert bot.consecutive_failures == 5
    assert bot.state == bot._KeeperState.SHUTTING_DOWN

    # close_run called exactly once
    bot._mock_db.close_run.assert_called_once()
    close_run_kwargs = bot._mock_db.close_run.call_args
    assert "failures=5" in close_run_kwargs[1].get("stop_reason", "") or \
           "failures=5" in str(close_run_kwargs)

    # Shutdown alert sent
    alert_calls = [str(c) for c in bot._mock_alert.call_args_list]
    assert any("🚨" in c for c in alert_calls), "Expected shutdown alert"
    assert any("🛑" in c for c in alert_calls), "Expected stopped alert"

    # Total stats
    assert bot.stats["failed"] == 5
    assert bot.stats["success"] == 0


# ---------------------------------------------------------------------------
# Bonus — No opportunity found
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_opportunity_returns_idle(bot):
    """Scanner returns None → bot stays IDLE, nothing else happens."""
    bot._mock_strategy.scan = AsyncMock(return_value=None)

    await bot.on_new_block(BLOCK_NUMBER)

    assert bot.state == bot._KeeperState.IDLE
    assert bot.stats["opportunities"] == 0
    assert bot.stats["success"] == 0
    bot._mock_db.save_opportunity.assert_not_called()
    bot._mock_submit.assert_not_called()
