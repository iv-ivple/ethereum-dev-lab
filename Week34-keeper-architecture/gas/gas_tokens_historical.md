# Gas Tokens: Historical Context & EVM Storage Economics

## Overview

Gas tokens (primarily **GST2** and **CHI**) were a clever pre-EIP-1559 arbitrage trick that
exploited the EVM's SSTORE refund mechanism. They are now obsolete, but studying them reveals
fundamental truths about EVM storage economics that still apply today.

---

## How SSTORE Refunds Worked Pre-EIP-3529

Before the London hard fork (August 2021), the EVM rewarded you for *freeing* storage. The
refund rules were:

| Operation | Gas Cost | Refund |
|---|---|---|
| Writing non-zero → zero (clearing a slot) | 5,000 gas | 15,000 gas refund |
| SELFDESTRUCT (destroying a contract) | 5,000 gas | 24,000 gas refund |

Critically, refunds were capped at **50% of the total gas used in the transaction**. This
meant that for a sufficiently gas-heavy transaction (e.g., a complex DeFi interaction costing
200,000 gas), you could receive up to 100,000 gas worth of refunds — effectively halving your
fee bill.

This created an arbitrage opportunity across *time*: if gas prices today are low, you can
pre-pay to create storage now and cash in those refunds later when gas prices are high.

---

## The GST2 Mechanism

**GST2** (Gas Savings Token 2, deployed by 1inch) was the dominant gas token. Here's how it worked:

### Minting (during cheap gas periods)
Calling `mint(amount)` caused the contract to write `amount` non-zero values into storage
slots. Each slot write cost ~20,000 gas (SSTORE on a cold, empty slot). You were essentially
*purchasing stored refunds* at a low price.

```
mint(100) → writes 100 storage slots → costs ~2,000,000 gas at 1 Gwei = 0.002 ETH
```

### Burning (during expensive gas periods)
Calling `free(amount)` during a high-fee transaction triggered SELFDESTRUCT on mini-contracts
or cleared storage slots, generating the refund. Because the refund cap was 50%, you needed
the surrounding transaction to be expensive enough to absorb the full refund.

```
High-fee swap (400,000 gas used) + burn(100 GST2) → up to 200,000 gas refunded
Net effective gas used: 200,000 gas, at a price you pre-paid at ~1 Gwei
```

**CHI Token** (also by 1inch) worked similarly but was optimized to use `SELFDESTRUCT`-based
refunds rather than storage clearing, making it slightly more efficient.

### The Math
At its peak, gas tokens could save 40–50% of transaction fees during high-congestion periods.
For MEV bots and high-frequency traders executing hundreds of transactions per day, this was
a meaningful edge.

---

## Why EIP-3529 (London, August 2021) Killed Gas Tokens

EIP-3529 made two targeted changes that eliminated the gas token model entirely:

### 1. Refund cap slashed from 50% → 20%
The maximum refund you can receive in a transaction dropped from 50% to 20% of gas used.
This alone made gas tokens far less profitable, since the high-fee transactions that justified
burning tokens could only absorb a fraction of their previous refund value.

### 2. SELFDESTRUCT refund eliminated
The 24,000 gas refund for `SELFDESTRUCT` was removed entirely. Since CHI and some GST2
strategies depended on this, they became unprofitable overnight.

### 3. SSTORE clearing refund reduced
The 15,000 gas refund for clearing a storage slot was reduced to 4,800 gas, further eroding
the economics.

**Net effect:** The cost to mint tokens could no longer be recovered through refunds during
realistic transaction scenarios. Gas tokens became net-negative.

### Why were these refunds added in the first place?
The original design intention was to incentivize developers to clean up state — deleting
storage slots returns capacity to the network. Gas tokens were an unintended exploit of this
incentive that actually *increased* state bloat (by minting millions of useless storage slots).
EIP-3529 corrected the incentive without fully removing the cleanup reward.

---

## The Lesson That Remains: SSTORE Economics Still Matter

Gas tokens are dead, but the underlying insight survives: **SSTORE is one of the most
expensive operations in the EVM, and your storage access patterns dramatically affect gas costs.**

### Warm vs. Cold Storage (EIP-2929, Berlin 2021)

| Access Type | SLOAD Cost | SSTORE Cost (first write) |
|---|---|---|
| Cold (first access in tx) | 2,100 gas | 22,100 gas |
| Warm (already accessed this tx) | 100 gas | 100 gas (if already dirty) |

Once a storage slot has been read or written in a transaction, it's "warm." Subsequent
accesses cost 100 gas instead of 2,100+.

### The Dirty-Write Pattern

This is the modern equivalent of gas token thinking. If you're going to write to the same
slot multiple times in one transaction, **the second write costs only 100 gas**:

```solidity
// EXPENSIVE: two cold-to-warm writes (if storage changes between them)
balances[user] += amount1;  // 22,100 gas (cold SSTORE)
// ... other logic ...
balances[user] += amount2;  // 2,900 gas (warm, but going nonzero→nonzero)

// EFFICIENT: compute once, write once
uint256 newBalance = balances[user] + amount1 + amount2;  // 2,100 gas SLOAD
balances[user] = newBalance;  // 22,100 gas SSTORE (one write)
```

### Design Principles for Gas-Efficient Solidity

1. **Batch all state changes to the same slot** — compute the final value in memory, then
   write once at the end of the function.

2. **Use `memory` copies of storage structs** — read a struct into memory once, mutate the
   memory copy, write back once.

   ```solidity
   // Good: 1 cold SLOAD + 1 SSTORE
   Position memory pos = positions[user];  // load struct to memory
   pos.amount += delta;
   pos.lastUpdated = block.timestamp;
   positions[user] = pos;  // single write-back
   ```

3. **Understand slot packing** — Solidity packs multiple variables under 32 bytes into a
   single storage slot. Writing to two packed variables in the same slot costs one SSTORE,
   not two. Layout your structs with packing in mind.

4. **Use access lists (EIP-2930)** — If you know which storage slots a transaction will
   touch, declare them in the access list. The slots start warm, saving 2,000 gas per SLOAD
   on the first access.

5. **Avoid storage in loops** — A loop that reads or writes storage on every iteration is a
   gas disaster. Cache to memory before the loop, write back after.

---

## Summary

| Era | Mechanism | Status |
|---|---|---|
| Pre-London (before Aug 2021) | SSTORE refunds up to 50%, gas tokens viable | Obsolete |
| Post-London (EIP-3529) | Refund cap 20%, SELFDESTRUCT refund removed | Gas tokens dead |
| Today (EIP-2929 + EIP-2930) | Warm/cold slot distinction, access lists | Active — design around these |

Gas tokens were a fascinating arbitrage on EVM incentives, and their elimination was a
deliberate choice to reduce state bloat. The takeaway for modern Solidity development is
the same instinct: treat SSTORE writes as expensive, batch them, and understand warm vs.
cold access patterns when estimating your contracts' gas profiles.
