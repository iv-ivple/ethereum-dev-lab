# EVM Gas Optimization — Week 31 Notes

## 1. EIP-1559 Fee Flow

```
Transaction submitted
│
├─ baseFeePerGas      → BURNED (removed from ETH supply forever)
├─ maxPriorityFeePerGas (tip) → VALIDATOR (block proposer)
└─ maxFeePerGas       → ceiling; unused portion REFUNDED to sender
```

**Key relationships:**

```
maxFeePerGas >= baseFeePerGas + maxPriorityFeePerGas   (required)
effective_gas_price = min(maxFeePerGas, baseFeePerGas + maxPriorityFeePerGas)
amount_paid = effective_gas_price × gas_used
amount_burned = baseFeePerGas × gas_used
validator_tip = (effective_gas_price - baseFeePerGas) × gas_used
```

**Base fee adjustment rule:**
- Previous block > 15M gas target → base fee increases up to +12.5%
- Previous block < 15M gas target → base fee decreases up to -12.5%
- This means a 2x base fee buffer covers ~6 consecutive full blocks

---

## 2. Opcode Cost Reference (post-EIP-2929 / Berlin)

| Category    | Opcode / Operation         | Gas Cost        | Notes                                      |
|-------------|----------------------------|-----------------|--------------------------------------------|
| Cheap       | ADD, SUB                   | 3               | Basic arithmetic                           |
| Cheap       | MUL, DIV                   | 5               | Slightly more expensive                    |
| Cheap       | Stack ops (PUSH, POP, DUP) | 2–3             | Cheapest operations                        |
| Medium      | SLOAD (cold)               | 2,100           | First access to a storage slot in the tx   |
| Medium      | SLOAD (warm)               | 100             | Subsequent accesses (EIP-2929)             |
| Medium      | SSTORE (new slot)          | 20,000          | Writing to a previously-zero slot          |
| Medium      | SSTORE (update)            | 2,900           | Changing an already-set slot               |
| Medium      | SSTORE refund (zero out)   | 4,800           | Gas refund for clearing a slot             |
| Medium      | CALL (cold account)        | 2,600           | First call to a contract address           |
| Medium      | CALL (warm account)        | 100             | Subsequent calls to same address           |
| Medium      | LOG0                       | 375             | Event with no topics                       |
| Medium      | LOG per byte               | 8               | Per byte of event data                     |
| Expensive   | Contract creation          | 32,000          | Base cost; plus init code execution        |
| Expensive   | SHA3 (base)                | 30              | Keccak256 base cost                        |
| Expensive   | SHA3 (per word)            | 6               | Per 32-byte word of input                  |
| Tx overhead | TX_BASE                    | 21,000          | Every transaction, regardless of operation |
| Tx overhead | Calldata zero byte         | 4               | Per 0x00 byte in calldata                  |
| Tx overhead | Calldata non-zero byte     | 16              | Per non-zero byte in calldata              |

---

## 3. Memory Expansion Cost

Memory in the EVM is cheap initially but expands quadratically. Cost is calculated in 32-byte *words*.

```
memory_size_words = ceil(bytes_needed / 32)

memory_cost = (memory_size_words² / 512) + (3 × memory_size_words)
```

**Practical examples:**

| Memory used | Words | Cost (gas) |
|-------------|-------|------------|
| 32 bytes    | 1     | 3          |
| 320 bytes   | 10    | 30 + 0.19 ≈ 30 |
| 1,024 bytes | 32    | 96 + 2 = 98 |
| 32,768 bytes| 1,024 | 3,072 + 2,048 = 5,120 |

The quadratic term becomes painful above ~1KB of memory. Avoid unbounded loops that grow memory.

---

## 4. Worked Example — ERC-20 Transfer Cost Breakdown

**Scenario:** Alice sends 100 USDC to Bob via `transfer(address, uint256)`.

### Layer 1 — Transaction base cost
```
TX_BASE = 21,000 gas
```

### Layer 2 — Calldata cost
Function call: `transfer(address to, uint256 amount)`
```
Function selector:  4 bytes  (non-zero) →   4 × 16 =  64 gas
to (address):      32 bytes  (12 leading zeros + 20 addr bytes)
                   → 12 × 4 + 20 × 16 = 48 + 320 = 368 gas
amount (uint256):  32 bytes  (mostly non-zero for a real value)
                   → ~28 × 16 + 4 × 4 = 448 + 16 = 464 gas

Calldata subtotal ≈ 896 gas
```

### Layer 3 — ERC-20 contract execution
```
SLOAD balances[from]        → 2,100 (cold) or 100 (warm)
SSTORE balances[from] (dec) →   2,900 (update existing)
SLOAD balances[to]          → 2,100 (cold) or 100 (warm)
SSTORE balances[to]   (inc) → 20,000 (new slot) or 2,900 (update)
Transfer event (LOG3)       →   375 + (3 × 375 topics) + (64 bytes × 8)
                            =   375 + 1,125 + 512 = 2,012 gas
Arithmetic + stack ops      → ~1,000–2,000 gas
```

**Worst case (cold storage, recipient has no balance):**
```
21,000 + 896 + 2,100 + 2,900 + 2,100 + 20,000 + 2,012 + 1,500 ≈ 52,508 gas
```

**Typical real-world cost:**
```
~46,000–65,000 gas
(Etherscan reports median ~46K for plain ERC-20 transfers)
```

The variance comes from whether slots are cold/warm (EIP-2929 access lists help here)
and whether the recipient has an existing balance.

---

## 5. Key Optimization Principles

**Storage (biggest wins):**
- Pack multiple small values into a single `uint256` slot (saves 20,000 gas per slot avoided)
- Use `uint128` pairs instead of two `uint256` values in structs
- Clear slots you no longer need — you get a 4,800 gas refund

**Calldata:**
- Prefer zero bytes — 4 gas vs 16 gas per byte
- Use compact ABI encoding for off-chain signatures
- Keep function signatures short at scale (4-byte selectors are fixed, but parameter types matter)

**Access patterns:**
- Use EIP-2930 access lists to pre-warm storage slots (reduces cold SLOAD 2,100 → 100)
- Batch reads/writes to the same slot within one transaction

**Gas limits:**
- Always add 10–20% buffer above `eth_estimateGas` — OOG reverts waste all gas
- Monitor transactions where `gasUsed == gasLimit` — these are out-of-gas failures

---

## 6. EIP Timeline Reference

| EIP   | Hard Fork | What changed                                           |
|-------|-----------|--------------------------------------------------------|
| 2028  | Istanbul  | Calldata zero byte: 68→4 gas, non-zero: 68→16 gas     |
| 2929  | Berlin    | Cold SLOAD: 800→2100; cold CALL: 700→2600              |
| 2930  | Berlin    | Optional access lists to pre-warm slots                |
| 1559  | London    | Base fee + burn model replaces single-price auction    |
| 3529  | London    | Reduced gas refunds (SELFDESTRUCT + SSTORE clear)      |
