# Keeper Bot Architecture — Research Notes
### Day 1 Study: Four Real Keeper Implementations
> Repos studied: Euler liquidation bot, MakerDAO dss-cron, Chainlink Keeper, Flashbots searcher-sponsored-tx

---

## 1. Euler Liquidation Bot
**Repo:** `euler-xyz/euler-liquidation-bot`
**Language:** JavaScript (Node.js)
**Architecture style:** Off-chain bot, centralised logic, WebSocket-driven

### How it listens for on-chain events
WebSocket subscription to Euler's own indexing service (`eulerscan`), not raw chain events. The bot connects to `wss://escan-mainnet.euler.finance` and subscribes to a live feed of accounts sorted by health score. The server pushes JSON patch diffs (not full state) whenever an account's health changes. This is efficient but introduces a **centralised dependency** — if Eulerscan goes down, the bot is blind.

### What triggers an opportunity
A health score below `1,000,000` (representing 1.0 in 18-decimal fixed point — i.e. undercollateralised). Profitability is checked second: yield from liquidation must exceed gas cost plus a configurable minimum ETH threshold (`minYield`, default `0.05 ETH`). The bot computes all collateral/liability pairs via a cartesian product and picks the highest-yield strategy.

### Transaction submission and retries
No automatic tx retry loop. Failed or unprofitable opportunities result in the account being **deferred** in memory for a fixed window:
- Liquidation error → 5 minutes
- No opportunity found → 5 minutes
- Yield too low → 10 minutes
- Insufficient collateral → 20 minutes

Gas uses live EIP-1559 fee data with an optional multiplier (`TX_FEE_MUL` env var) for aggressive submission. An `inFlight` boolean flag prevents concurrent liquidation attempts.

### State persistence
**In-memory only.** `subsData` holds all account states, updated via patches. `deferredAccounts` is an in-memory map with expiry timestamps. A log file (`log.txt`) records outcomes on mainnet but is not used for recovery. **A crash loses all deferred state** — the bot restarts cold.

### Patterns to note
- ✅ Patch-based diffs are bandwidth-efficient
- ✅ Exponential backoff reconnect (500ms → 8s ceiling) with automatic subscription replay
- ✅ Heartbeat ping every 55s to detect silent WebSocket drops
- ⚠️ Depends on a centralised indexer — not trustless
- ⚠️ No persistent state — crash = cold restart
- ⚠️ No tx retry — missed opportunity just defers

---

## 2. MakerDAO dss-cron
**Repo:** `makerdao/dss-cron`
**Language:** Solidity (Foundry project)
**Architecture style:** On-chain logic, off-chain keeper is nearly brainless

### How it listens for on-chain events
It doesn't — it uses **block number as a clock**. The `Sequencer` contract computes which keeper network is "master" at any given block using modular arithmetic:

```solidity
uint256 pos = block.number % totalWindowSize;
return window.start <= pos && pos < window.start + window.length;
```

The off-chain keeper polls every block, checks `isMaster()`, and if true, calls `getNextJobs()` to discover what's workable.

### What triggers an opportunity
Two-layer check. First, the network must be the current master (enforced on-chain). Second, each `Job` contract independently decides if it's ready — `TimedJob` checks `block.timestamp >= last + maxDuration`, and `OracleJob` simulates poking every oracle with `try/catch` to see if any spot price would change. The **contract tells the keeper what to do**, not the other way around.

### Transaction submission and retries
No explicit retry logic needed. The block window system is the retry mechanism — if a keeper misses its window (crash, gas failure), it simply waits for the next rotation. `OracleJob` uses `try/catch` per ilk so one bad oracle doesn't block the rest, and only reverts if zero ilks succeeded (`if (numSuccessful == 0) revert NotSuccessful()`).

### State persistence
**On-chain, permanently.** `TimedJob` stores `last` (timestamp of last successful execution) in contract storage. No database, no files, no in-memory state. The off-chain keeper can crash and restart anytime — the contracts always reflect ground truth.

### Patterns to note
- ✅ Crash-proof by design — all state is on-chain
- ✅ Multiple keeper networks co-ordinated without racing (block windows)
- ✅ Adding a new protocol action = deploy a new Job contract, no bot code changes
- ✅ `try/catch` per asset = partial success is fine, one bad oracle doesn't break the batch
- ⚠️ Block window coordination requires governance to configure window sizes correctly
- ⚠️ Off-chain keeper must still poll every block — slightly wasteful

---

## 3. Chainlink Keeper / Automation Node
**Repo:** `smartcontractkit/chainlink` — `core/services/keeper/`
**Language:** Go
**Architecture style:** Production-grade node with database, dual event/polling, parallelised execution

### How it listens for on-chain events
Both — **on-chain log events AND periodic polling**, running in parallel in the same select loop:

```go
select {
case <-syncTicker.Ticks():   // periodic full resync
    rs.fullSync(ctx)
case <-rs.mbLogs.Notify():   // react to on-chain log events
    rs.processLogs(ctx)
}
```

`RegistrySynchronizer` registers as a log listener for registry contract events. `UpkeepExecuter` separately subscribes to every new block head via `headBroadcaster`. Logs give speed; polling gives reliability against missed events and reorgs.

### What triggers an opportunity
Three-layer check. First, **turn-taking via block hash binary**: a historical block hash is converted to a binary string and used to assign upkeeps to keepers pseudo-randomly but deterministically — fair without coordination. Second, a **database query** filters upkeeps that are due based on `LastRunBlockHeight` and `MaxGracePeriod`. Third, the **pipeline** calls `checkUpkeep()` on-chain to confirm the upkeep actually needs performing before submitting `performUpkeep()`.

### Transaction submission and retries
Execution is parallelised with a bounded goroutine queue of size 10. Each execution has a 1-minute timeout. Retry is implicit — if a tx fails, `LastRunBlockHeight` is not updated in the database, so the upkeep remains eligible and the next block triggers another attempt automatically. Prometheus metrics track execution time per upkeep (`keeper_check_upkeep_execution_time`).

### State persistence
**PostgreSQL via ORM.** `Registry` and `UpkeepRegistration` are fully database-backed structs, including `KeeperIndexMap` stored as JSON. `LastRunBlockHeight` in the database is the canonical source of truth for retry decisions. Restart the node and it picks up exactly where it left off.

### Patterns to note
- ✅ Dual listening (logs + polling) is the most robust approach
- ✅ Block hash turn-taking is elegant — fair, deterministic, no on-chain coordination needed
- ✅ Implicit retry via database state is clean and crash-safe
- ✅ Bounded parallelism (queue of 10) prevents overload while still being fast
- ✅ Prometheus metrics built in — production observability from day one
- ⚠️ Most complex to operate — requires a running PostgreSQL instance
- ⚠️ Go codebase with pipeline abstraction has a steep learning curve

---

## 4. Flashbots Searcher
**Repo:** `flashbots/searcher-sponsored-tx`
**Language:** TypeScript
**Architecture style:** Stateless MEV searcher, private relay, atomic bundle submission

### How it listens for on-chain events
Simple block polling via ethers.js `provider.on('block', ...)`. No event subscriptions. The opportunity is identified once upfront before the polling loop starts — the loop just resubmits every block until the bundle lands.

### What triggers an opportunity
The opportunity is pre-identified before the main loop. An "engine" class (extending `Base`) implements `getSponsoredTransactions()` to build the transaction list. The loop continuously resubmits targeting `currentBlock + 2`. This is appropriate for MEV — you already know the opportunity; the challenge is getting included before someone else.

### Transaction submission and retries
Three explicit bundle resolution outcomes handled per block:
- `BundleIncluded` → exit cleanly
- `BlockPassedWithoutInclusion` → loop continues, resubmit next block automatically
- `AccountNonceTooHigh` → bail

Every submission is preceded by a **simulation** (`flashbotsProvider.simulate()`) that checks for reverts and verifies `coinbaseDiff > 0` (miner is being paid). If simulation fails, the bundle is not submitted. This prevents wasted relay calls.

### State persistence
**Entirely stateless.** Bundle is built once in memory, signed once, resubmitted from memory every block. No database, no files. Crash and restart cleanly.

### The sponsored transaction pattern
The key architectural insight: bundles use two wallets so the **executor wallet can hold assets with zero ETH**. The sponsor funds gas atomically in TX #0; if it fails, the whole bundle reverts. If the bundle isn't included, nothing happens — no gas wasted, no state changed. Atomicity is the guarantee.

```
Bundle = [
  TX #0: sponsor  → executor   (ETH for gas, exact amount)
  TX #1: executor → contract   (the actual action)
  TX #N: executor → ...        (additional actions)
]
```

### Patterns to note
- ✅ Private relay = MEV-protected, no frontrunning from public mempool
- ✅ Simulate before every submission = never waste a relay call
- ✅ All-or-nothing atomicity = safe to resubmit aggressively
- ✅ Sponsored tx pattern = executor wallet needs zero ETH
- ✅ Engine abstraction (`Base`) makes it trivial to plug in new opportunity logic
- ⚠️ Stateless resubmission only works if the opportunity doesn't change block-to-block
- ⚠️ Depends on Flashbots relay being live and builders accepting bundles

---

## Cross-Cutting Patterns — Summary

### Event listening strategies
| Approach | Used by | Pros | Cons |
|---|---|---|---|
| WebSocket push (indexer) | Euler | Low latency, efficient | Centralised dependency |
| Block polling | MakerDAO, Flashbots | Simple, no subscription | Slightly slower, polls every block |
| Logs + polling (dual) | Chainlink | Fast AND reliable | More complex to implement |

**Decision for my bot:** Use dual approach (logs as primary, polling as fallback) for any bot where missing an event is costly. For lower-stakes bots, block polling is fine.

### Trigger / opportunity detection
| Approach | Used by | Notes |
|---|---|---|
| Off-chain threshold check | Euler | Health score < 1.0 computed from indexer data |
| On-chain workable() | MakerDAO | Contract decides; keeper just asks |
| DB query + on-chain confirm | Chainlink | Two-step: DB filters candidates, chain confirms |
| Pre-identified + resubmit | Flashbots | Opportunity found once, loop just lands it |

**Decision for my bot:** For liquidation bots, a two-step approach (cheap off-chain filter → on-chain confirm) is the right balance of efficiency and correctness.

### State persistence
| Approach | Used by | Crash behaviour |
|---|---|---|
| In-memory | Euler | Cold restart, lose deferred state |
| On-chain | MakerDAO | Perfect recovery, but gas to write state |
| Database (PostgreSQL) | Chainlink | Full recovery, operationally complex |
| Stateless | Flashbots | No state to recover |

**Decision for my bot:** SQLite for local development (simpler than PostgreSQL), migrate to PostgreSQL for production. Never rely solely on in-memory state for anything that matters.

### Competition / coordination
| Approach | Used by | Notes |
|---|---|---|
| Race (first wins) | Euler | Simple but gas-inefficient under competition |
| Block windows (on-chain) | MakerDAO | Requires governance, zero racing |
| Block hash turn-taking | Chainlink | Elegant, no coordination needed |
| Private relay (Flashbots) | Flashbots | Best for MEV — no public competition |

**Decision for my bot:** For a liquidation bot competing against others, consider submitting via Flashbots to avoid gas wars. For protocol maintenance jobs (cron-style), a MakerDAO-style sequencer is cleaner.

### Retry strategies
| Approach | Used by | Notes |
|---|---|---|
| Defer N minutes (in-memory) | Euler | Simple, loses state on crash |
| Next window automatically | MakerDAO | No retry code needed |
| Implicit via DB state | Chainlink | Clean, crash-safe, no explicit retry loop |
| Every block (resubmit) | Flashbots | Aggressive, works because atomic |

**Decision for my bot:** Implicit retry via persistent state (Chainlink-style) is the cleanest. Avoid time-based deferral in memory.

---

## Patterns to Adopt

1. **Dual listening** — register for log events AND run a periodic sync. Logs for speed, sync for correctness.
2. **Simulate before submitting** — always call `eth_call` or Flashbots simulate before sending a tx. Never waste gas on a tx that will revert.
3. **Bounded parallelism** — process multiple opportunities concurrently but cap the queue (Chainlink uses 10). Prevents overload.
4. **Implicit retry via persistent state** — don't write retry loops. Instead, only update "last run" state after confirmed success. Eligible = not yet successful.
5. **Sponsored tx / Flashbots bundles** — for competitive liquidation, private relay submission eliminates gas wars and frontrunning.
6. **Engine/strategy abstraction** — separate opportunity detection from execution (Flashbots `Base`, Euler strategies). Makes it easy to add new opportunity types without touching core bot logic.
7. **Heartbeat / keepalive** — any long-lived WebSocket connection needs a periodic ping and exponential backoff reconnect with subscription replay.
8. **On-chain workable()** — for protocol maintenance jobs, put the trigger condition in a contract. Keeper asks; contract answers. Cleaner separation of concerns.

## Patterns to Avoid

1. **In-memory-only state** — losing deferred accounts on crash is acceptable for a toy bot, unacceptable in production.
2. **Single centralised indexer dependency** — Euler's reliance on Eulerscan is a single point of failure. Prefer raw chain events or your own indexer.
3. **Unbounded parallelism** — spawning a goroutine/promise per opportunity with no queue is a DoS vector against yourself.
4. **Public mempool for competitive opportunities** — any liquidation bot that submits to the public mempool will be frontrun. Use Flashbots or a private RPC.
5. **Polling-only for time-sensitive triggers** — polling every block is fine for maintenance jobs, too slow for liquidations where milliseconds matter.
6. **No observability** — Euler has a log file, Flashbots has console logs. Chainlink has Prometheus. Build metrics in from day one.

---

## Open Questions for Day 2

- What does a minimal SQLite-backed state store look like for a liquidation bot?
- How do I structure my own `workable()` / `work()` interface for pluggable job types?
- Which Flashbots bundle construction patterns translate directly to a liquidation use case?
- How does the Chainlink block hash turn-taking algo behave under chain reorgs?
- What's the gas overhead of the sponsored tx pattern vs direct submission?
