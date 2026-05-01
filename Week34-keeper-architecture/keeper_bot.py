import asyncio
import logging
from web3 import Web3
from keeper.state_machine import KeeperState
from keeper.config import config
from keeper.logging_config import setup_logging
from keeper.listener.block_listener import BlockListener
from keeper.database.state_store import StateStore
from keeper.alerting.telegram_alert import send_alert
from keeper.calculator.profitability import is_profitable
from keeper.executor.tx_builder import build_tx
from keeper.executor.tx_signer import sign_tx
from keeper.executor.tx_submitter import submit_and_confirm
from keeper.strategies.arb_strategy import ArbStrategy
from keeper.health_server import start_health_server

logger = setup_logging()

class KeeperBot:
    def __init__(self):
        config.validate()
        self.w3 = Web3(Web3.HTTPProvider(config.rpc_http_url))
        self.state = KeeperState.IDLE
        self.strategy = ArbStrategy()
        self.db = StateStore(config.database_url)
        self.run_id = self.db.open_run()
        self.consecutive_failures = 0
        self.stats = {"blocks": 0, "opportunities": 0, "success": 0, "failed": 0, "profit": 0.0}

    async def on_new_block(self, block_number: int):
        """Called by BlockListener on every new block."""
        self.stats["blocks"] += 1
        self.state = KeeperState.SCANNING

        try:
            opportunity = await self.strategy.scan(block_number)
            if opportunity is None:
                self.state = KeeperState.IDLE
                return

            self.stats["opportunities"] += 1
            self.state = KeeperState.OPPORTUNITY_FOUND
            profitable, reason = is_profitable(opportunity)

            if not profitable:
                logger.info(f"Opportunity skipped: {reason}")
                self.db.save_opportunity(opportunity, status="skipped", run_id=self.run_id)
                self.state = KeeperState.IDLE
                return

            # Build, sign and submit transaction
            self.state = KeeperState.EXECUTING
            nonce = self.w3.eth.get_transaction_count(config.keeper_address)
            tx = build_tx(opportunity, self.w3, nonce)
            raw_tx = sign_tx(tx, self.w3)

            opp_id = self.db.save_opportunity(opportunity, status="executing", run_id=self.run_id)
            self.state = KeeperState.CONFIRMING

            receipt = await submit_and_confirm(raw_tx, self.w3, config.tx_confirm_timeout_blocks)

            # Success
            self.stats["success"] += 1
            self.stats["profit"] += opportunity.net_profit_eth
            self.consecutive_failures = 0
            self.db.update_opportunity_status(opp_id, "success", tx_hash=receipt["transactionHash"].hex())
            await send_alert(f"✅ Keeper success | {opportunity.description} | profit: {opportunity.net_profit_eth:.5f} ETH")
            self.state = KeeperState.IDLE

        except Exception as e:
            self.stats["failed"] += 1
            self.consecutive_failures += 1
            logger.error(f"Execution failed: {e}", extra={"state": str(self.state)})
            await send_alert(f"❌ Keeper failure #{self.consecutive_failures}: {e}")

            if self.consecutive_failures >= config.max_consecutive_failures:
                logger.critical("Too many consecutive failures. Shutting down.")
                await send_alert(f"🚨 Keeper shutting down after {self.consecutive_failures} failures")
                self.state = KeeperState.SHUTTING_DOWN
                await self.shutdown()
                return

            self.state = KeeperState.COOLDOWN
            await asyncio.sleep(config.cooldown_seconds)
            self.state = KeeperState.IDLE

    async def run(self):
        logger.info("Keeper bot starting", extra={"state": "starting"})
        await send_alert("🤖 Keeper bot started")
        start_health_server(self.stats)
        listener = BlockListener(config.rpc_ws_url, self.on_new_block)
        await asyncio.gather(
            listener.start(),
            self.stats_reporter(),
        )

    async def shutdown(self):
        self.db.close_run(self.run_id, stop_reason=f"failures={self.consecutive_failures}", stats=self.stats)
        await send_alert(f"🛑 Keeper stopped. Stats: {self.stats}")

    async def stats_reporter(self):
        """Background task: send stats to Telegram every hour."""
        while self.state != KeeperState.SHUTTING_DOWN:
            await asyncio.sleep(3600)
            eth_balance = self.w3.eth.get_balance(config.keeper_address)
            eth_balance_ether = self.w3.from_wei(eth_balance, "ether")
            report = (
                f"📊 <b>Keeper Stats (last hour)</b>\n"
                f"Blocks scanned: {self.stats['blocks']}\n"
                f"Opportunities found: {self.stats['opportunities']}\n"
                f"Executed successfully: {self.stats['success']}\n"
                f"Failed: {self.stats['failed']}\n"
                f"Total profit: {self.stats['profit']:.5f} ETH\n"
                f"Wallet balance: {eth_balance_ether:.4f} ETH"
            )
            await send_alert(report)
            # Reset hourly counters but not totals
            self.stats = {k: 0 for k in self.stats}

if __name__ == "__main__":
    asyncio.run(KeeperBot().run())
