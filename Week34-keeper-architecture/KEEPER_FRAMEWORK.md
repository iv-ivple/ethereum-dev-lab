# Keeper Framework

A modular, strategy-agnostic keeper bot for Ethereum. Plug in any on-chain strategy — arbitrage, liquidations, limit orders — without touching the core execution pipeline.

---

## Architecture

```
WebSocket (RPC_WS_URL)
    │
    ▼
BlockListener ──► KeeperBot.on_new_block(block_number)
                        │
                        ▼
                  BaseScanner.scan()        ← your strategy lives here
                        │
                  ┌─────┴──────────┐
                  │                │
               No opp.          Opportunity
                  │                │
               IDLE          is_profitable()?
                                   │
                           ┌───────┴───────┐
                           │               │
                         False           True
                           │               │
                      log + DB         build_tx()
                      (skipped)            │
                          │            sign_tx()
                        IDLE               │
                                   submit_and_confirm()
                                         │
                                  ┌──────┴──────┐
                                  │             │
                               Success       Failure
                                  │             │
                             log + alert   increment counter
                             DB update          │
                                  │      ┌──────┴──────┐
                                IDLE     │             │
                                    cooldown    max failures?
                                         │             │
                                       IDLE      SHUTTING_DOWN
                                                      │
                                               close_run() + alert
```

### Key components

| Module | Responsibility |
|---|---|
| `keeper/listener/block_listener.py` | WebSocket subscription, auto-reconnect on disconnect |
| `keeper/scanner/opportunity_scanner.py` | `BaseScanner` ABC — implement `scan()` for each strategy |
| `keeper/calculator/profitability.py` | Min profit, gas ceiling, ROI floor checks |
| `keeper/executor/` | `build_tx` → `sign_tx` → `submit_and_confirm` pipeline |
| `keeper/database/state_store.py` | `StateStore` class — persists opportunities and run stats |
| `keeper/alerting/` | Telegram and Discord alert helpers |
| `keeper/health_server.py` | Flask `/health` endpoint — live stats without tailing logs |
| `keeper_bot.py` | Orchestrator — wires all components, owns the state machine |
| `scripts/analyze_logs.py` | Post-run log analyser — errors, state transitions, profit summary |

---

## Quickstart

Get the bot running with any strategy in under 5 minutes.

**1. Clone and install dependencies**

```bash
git clone https://github.com/iv-ivplus/ethereum-dev-lab
cd ethereum-dev-lab/Week34-keeper-architecture
pip install -r requirements.txt
```

**2. Configure environment**

```bash
cp .env.example .env
# Edit .env — minimum required vars:
#   RPC_URL, RPC_WS_URL, KEEPER_ADDRESS, PRIVATE_KEY
```

**3. Create the database tables**

```bash
python scripts/migrate_keeper_db.py
```

**4. Run the bot**

```bash
python keeper_bot.py
```

**5. Check health in a second terminal**

```bash
curl http://localhost:8080/health
# {"blocks": 12, "opportunities": 3, "success": 2, "failed": 0, "profit": 0.00431}
```

**6. Analyse logs after a run**

```bash
python scripts/analyze_logs.py
# Parses structured JSON logs and prints a summary of errors, state transitions, and profit per block
```

---

## Extending the Framework

Adding a new strategy takes three steps. The core pipeline never changes.

### Step 1 — Implement `BaseScanner`

Create a new file in `keeper/strategies/`:

```python
# keeper/strategies/liquidation_strategy.py
from typing import Optional
from keeper.scanner.opportunity_scanner import BaseScanner, Opportunity
from keeper.config import config

class LiquidationStrategy(BaseScanner):
    async def scan(self, block_number: int) -> Optional[Opportunity]:
        # Query Aave/Compound for undercollateralised positions
        positions = await fetch_liquidatable_positions()
        if not positions:
            return None

        best = max(positions, key=lambda p: p.net_profit_eth)
        if best.net_profit_eth < config.min_profit_eth:
            return None

        return Opportunity(
            strategy="liquidation_aave",
            description=f"Liquidate {best.borrower} on Aave",
            gross_profit_eth=best.gross_profit_eth,
            gas_cost_eth=best.gas_cost_eth,
            net_profit_eth=best.net_profit_eth,
            input_amount_eth=best.input_amount_eth,
            metadata={"borrower": best.borrower, "collateral": best.collateral},
        )
```

The only rule: return an `Opportunity` if one exists, `None` if not. The framework handles everything else.

### Step 2 — Register in `keeper_bot.py`

```python
# Before
from keeper.strategies.arb_strategy import ArbStrategy
...
self.strategy = ArbStrategy()

# After
from keeper.strategies.liquidation_strategy import LiquidationStrategy
...
self.strategy = LiquidationStrategy()
```

### Step 3 — Run and verify

```bash
python keeper_bot.py
curl http://localhost:8080/health
```

No other files need to change. The profitability check, tx pipeline, DB logging, and alerting all work automatically.

---

## Environment Variables Reference

All variables are read from `.env` at startup via `keeper/config.py`.

### Required

| Variable | Description | Example |
|---|---|---|
| `RPC_URL` | HTTP RPC endpoint for tx submission and balance queries | `https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY` |
| `RPC_WS_URL` | WebSocket RPC endpoint for block subscriptions | `wss://eth-mainnet.g.alchemy.com/v2/YOUR_KEY` |
| `KEEPER_ADDRESS` | Ethereum address the bot executes from | `0xYourAddress` |
| `PRIVATE_KEY` | Private key for signing transactions (keep secret) | `0xabc123...` |

### Profitability

| Variable | Description | Default |
|---|---|---|
| `MIN_PROFIT_ETH` | Minimum net profit to execute a trade | `0.002` |
| `MAX_GAS_GWEI` | Gas price ceiling — skips trade if base fee exceeds this | `50.0` |
| `SLIPPAGE_BPS` | Slippage tolerance in basis points (100 = 1%) | `50` |

### Reliability

| Variable | Description | Default |
|---|---|---|
| `MAX_FAILURES` | Consecutive failures before the bot shuts down | `5` |
| `COOLDOWN_SECONDS` | Seconds to wait after a failure before resuming | `30` |
| `CONFIRM_TIMEOUT_BLOCKS` | Blocks to wait for tx confirmation before timeout | `3` |

### Database

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///keeper.db` |

For Postgres: `postgresql://user:password@localhost:5432/keeper`

### Alerting (optional)

| Variable | Description | Default |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from @BotFather | `""` (disabled) |
| `TELEGRAM_CHAT_ID` | Telegram chat ID to send alerts to | `""` (disabled) |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for alerts | `""` (disabled) |

Alerting is silently disabled if tokens are not set — the bot runs fine without it.

---

## Alerting Guide

The bot sends structured alerts at key lifecycle events. Each emoji signals a distinct event type at a glance.

| Emoji | Event | When it fires |
|---|---|---|
| 🤖 | Bot started | Once at startup, after `config.validate()` passes |
| ✅ | Trade success | Tx confirmed on-chain, profit logged to DB |
| ❌ | Trade failed | Executor raised an exception (revert, timeout, RPC error) |
| 🚨 | Shutdown warning | Consecutive failure count hit `MAX_FAILURES` |
| 🛑 | Bot stopped | After `close_run()` — includes final stats summary |
| 📊 | Hourly stats | Every 60 minutes — blocks scanned, profit, wallet balance |

### Example alert messages

```
🤖 Keeper bot started

✅ Keeper success | WETH→USDC→DAI→WETH | profit: 0.00431 ETH

❌ Keeper failure #2: transaction reverted

🚨 Keeper shutting down after 5 failures

🛑 Keeper stopped. Stats: {'blocks': 1204, 'opportunities': 18, 'success': 11, 'failed': 5, 'profit': 0.0312}

📊 Keeper Stats (last hour)
Blocks scanned: 300
Opportunities found: 4
Executed successfully: 3
Failed: 1
Total profit: 0.00893 ETH
Wallet balance: 0.4821 ETH
```

### Tuning alert volume

If alerts are too noisy, raise `MIN_PROFIT_ETH` to filter out marginal opportunities before they reach the executor. The `📊` hourly report gives you the aggregate picture without per-trade noise.

---

## Running Tests

```bash
# Unit + config tests
pytest keeper/tests/ -v

# Integration pipeline tests (no real RPC needed)
pytest keeper/tests/integration/test_keeper_pipeline.py -v

# All tests
pytest -v
```

---

## Project Structure

```
Week34-keeper-architecture/
├── keeper_bot.py                  # Entry point
├── conftest.py                    # Pytest path + mock stubs
├── keeper/
│   ├── config.py                  # All settings from environment variables
│   ├── state_machine.py           # KeeperState enum + transitions
│   ├── logging_config.py          # Structured JSON logging
│   ├── health_server.py           # Flask /health endpoint
│   ├── listener/
│   │   ├── block_listener.py      # WebSocket block subscription
│   │   └── event_listener.py      # Contract event subscriptions
│   ├── scanner/
│   │   └── opportunity_scanner.py # BaseScanner ABC + Opportunity dataclass
│   ├── calculator/
│   │   └── profitability.py       # Profit, gas, ROI checks
│   ├── executor/
│   │   ├── tx_builder.py          # Build unsigned tx dicts
│   │   ├── tx_signer.py           # Sign with private key
│   │   └── tx_submitter.py        # Submit + handle replacement/speedup
│   ├── database/
│   │   ├── models.py              # SQLAlchemy models
│   │   └── state_store.py         # StateStore class + DB helpers
│   ├── alerting/
│   │   ├── telegram_alert.py      # Telegram bot integration
│   │   └── discord_alert.py       # Discord webhook integration
│   ├── strategies/
│   │   └── arb_strategy.py        # Triangle arbitrage (Week 28–30)
│   └── tests/
│       ├── test_config.py         # Config loading + validation
│       └── integration/
│           └── test_keeper_pipeline.py  # Full pipeline mock tests
└── scripts/
    ├── migrate_keeper_db.py       # Create DB tables (idempotent)
    └── analyze_logs.py            # Parse structured JSON logs, summarise errors + profit
```
