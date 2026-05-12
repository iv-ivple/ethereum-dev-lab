# MakerDAO Architecture — Week 41 Notes

> Covers Days 1–5: Whitepaper, Vault Mechanics, Collateralisation Ratios, Stability Fees, Oracle/OSM.
> Script outputs from live mainnet are embedded inline.

---

## 1. System Overview

### What MakerDAO Is

MakerDAO is a decentralised protocol that lets users lock collateral (e.g. ETH, WBTC) and mint **DAI** — a soft-pegged USD stablecoin — without a centralised custodian. Unlike USDT/USDC, DAI is not backed by off-chain dollars; it is backed by over-collateralised on-chain assets enforced by smart contracts.

**The problem it solves:** USDT/USDC require trusting a company (Tether, Circle) to hold real dollars and not freeze your account. DAI is censorship-resistant — anyone with ETH can mint it permissionlessly, and the peg is enforced by economic incentives encoded in contracts.

**SAI vs MCD:**
- **SAI (Single Collateral Dai):** original version, ETH-only collateral, now deprecated.
- **MCD (Multi Collateral Dai):** current system, multiple collateral types (`ilk`s), includes the DAI Savings Rate (DSR), and separates the stability fee logic into the Jug contract.

### Key Actors

| Actor | Role |
|---|---|
| **Vault owners** | Lock collateral, mint DAI, pay stability fees |
| **Keepers** | Bots that call `bark()` to trigger liquidations and `drip()` to update rates |
| **MKR holders** | Governance — vote on risk parameters (mat, line, duty); last-resort capital if system goes insolvent |
| **Oracle providers** | 14+ independent feeds → Median → OSM → Spot → Vat |

### Core Contract Map

```
Vat    — core accounting ledger: all collateral (ink) and debt (art) balances
Vow    — system surplus/deficit buffer (Maker Buffer)
Jug    — stability fee accrual; drip() updates rate accumulator per ilk
Dog    — liquidation engine: bark() marks a Vault unsafe, kicks off Clipper auction
Clip   — Dutch auction for liquidated collateral (price decreases over time)
Flap   — surplus auction: DAI → MKR burn (when surplus > hump + bump)
Flop   — debt auction: MKR mint → DAI (when bad debt > sump)
Spot   — oracle bridge: reads OSM price, divides by mat, writes ilk.spot to Vat
OSM    — Oracle Security Module: 1-hour delayed price feed
Pot    — DAI Savings Rate accumulator
```

---

## 2. Vault Mechanics (CDPs)

### Key Terms

| Term | Type | Meaning |
|---|---|---|
| `ilk` | `bytes32` | Collateral type identifier — e.g. `"ETH-A"`, `"WBTC-A"` |
| `urn` | struct | A single Vault, identified by `(ilk, owner_address)` |
| `ink` | WAD | Collateral locked in the Vault |
| `art` | WAD | **Normalised** debt — NOT raw DAI; must multiply by `rate` to get actual DAI owed |
| `rate` | RAY | Per-ilk stability fee accumulator; starts at `10^27`; grows over time |
| `spot` | RAY | Max DAI drawable per unit of collateral; `= oracle_price / mat` |
| `line` | RAD | Debt ceiling for the ilk |
| `dust` | RAD | Minimum debt — a Vault must borrow at least this much |

### Key Formulas

```
Actual debt (DAI)         = art × rate / RAY / WAD
Collateralisation ratio   = (ink × spot / RAY) / (art × rate / RAY) × 100%
Max drawable DAI          = ink × spot / RAY         (safety margin already in spot)
Unsafe condition          = ink × spot < art × rate  (integer, no division needed)
```

### Vault Lifecycle

```
open   → lock (deposit ink)
       → draw (mint DAI, art increases)
       → [wait, rate accrues]
       → wipe (repay DAI, art decreases)
       → free (withdraw ink)
       → close
```

If the Vault becomes unsafe (`ink × spot < art × rate`), a Keeper can call `Dog.bark()` to liquidate it.

### Worked Example — ETH-A at 150% mat

```
ETH price  = $3,000
mat        = 1.5   (150% liquidation ratio)
spot       = $3,000 / 1.5 = $2,000

Lock 2 ETH:
  Max drawable DAI  = 2 × $2,000 = $4,000
  Collateral value  = 2 × $3,000 = $6,000
  Collat ratio      = $6,000 / $4,000 = 150%   ← right at the minimum — don't do this

Safe to draw 3,000 DAI:
  Collat ratio      = $6,000 / $3,000 = 200%   ← healthy buffer
```

---

## 3. Live Ilk Parameters (from `read_ilk_params.py`)

```
ILK            Total Debt (DAI)         Rate     Spot ($)    Ceiling (M)   Dust (DAI)
-------------------------------------------------------------------------------------
ETH-A               168,066,853     33.8980%     1,585.02         314.2M        7,500
ETH-B                 8,252,064     41.3622%     1,767.90          28.9M       25,000
ETH-C               325,901,554     24.3691%     1,351.93         417.6M        3,500
WBTC-A                  847,181     43.4132%    54,101.79           0.0M        7,500
```

**Notes on this output:**
- The `Rate` column is the **accumulated** rate (total fees since deployment), not an annual fee — the 33% for ETH-A represents total compounded accrual since the ilk was created, not the current APY.
- `Spot ($)` is `oracle_price / mat` — it is *lower* than market price by the safety margin. ETH-A spot of $1,585 with mat=145% implies oracle price ≈ $2,298 (confirmed by OSM output below).
- WBTC-A ceiling is 0.0M — that ilk's debt ceiling has been set to zero (effectively deprecated or paused by governance).

---

## 4. Collateralisation Ratios — Spot Contract

**Script:** `read_spot.py`

```
ETH-A: mat=145%  oracle=0x81FE72B5A8d1A857d176C3E7d5Bd2679A9B85763
ETH-B: mat=130%  oracle=0x81FE72B5A8d1A857d176C3E7d5Bd2679A9B85763
ETH-C: mat=170%  oracle=0x81FE72B5A8d1A857d176C3E7d5Bd2679A9B85763
WBTC-A: mat=150%  oracle=0xf185d0682d50819263941e5f4EacC763CC5C6C42
```

**Interpretation:**
- ETH-A/B/C all use the same OSM oracle (`0x81FE...`) — different risk parameters, same price source.
- ETH-B has the lowest mat (130%) — more capital efficient but higher liquidation risk; compensated by higher stability fee.
- ETH-C has the highest mat (170%) — lowest risk, largest credit line, lowest stability fee. Targets conservative large borrowers.
- WBTC-A uses a separate OSM for BTC price.

**The formula chain (trace end-to-end):**

```
OSM price (USD, 1-hr delayed)
    ÷ mat (e.g. 1.45)
    = spot stored in Vat  ← max DAI per collateral unit, safety margin baked in
```

---

## 5. Stability Fees — Jug Contract

**Script:** `read_stability_fees.py` — **Script currently broken** (see bug note below).

### What it should return

The script reads `Jug.ilks(ilk_bytes)` → `(duty, rho)` and `Jug.base()` then computes:

```
base_annual   = (base / RAY)^31_536_000 - 1
annual_fee    = (duty / RAY)^31_536_000 - 1 + base_annual

Expected output format:
  Base rate: X.XXXX% per year

  ILK        Annual Stability Fee         Last Drip
  -------------------------------------------------------
  ETH-A              X.XXXX%      YYYY-MM-DD HH:MM
  ETH-B              X.XXXX%      YYYY-MM-DD HH:MM
  ETH-C              X.XXXX%      YYYY-MM-DD HH:MM
  WBTC-A             X.XXXX%      YYYY-MM-DD HH:MM
```

Based on the `rate` accumulator values from `read_ilk_params.py` and typical governance history, approximate current fees are: ETH-A ~3–5%, ETH-B ~5–8%, ETH-C ~0–2%, WBTC-A ~3–5%. **Fix the script to get exact live values.**

### Bug to fix

```
web3.exceptions.InvalidAddress: ENS name: '0x19c0976f590D67707E62397C87829d896Dc0f1F' is invalid.
```

**Root cause:** The Jug address in the script is missing its last character — it is 41 hex chars instead of 42. The correct checksummed address is:

```
0x19c0976f590D67707E62397C87829d896Dc0f1F  ← in script (41 chars — WRONG)
0x19c0976f590D67707E62397C87829d896Dc0f1F  ← needs verification
```

**Fix:** Use `Web3.to_checksum_address()` on the address, or grab the canonical address from https://chainlog.makerdao.com (key: `MCD_JUG`). The chainlog address should be the authority. Likely the script just needs the address corrected to its full checksum form.

### Key Concepts

```
duty   — per-ilk per-second rate multiplier (RAY), compounds continuously
base   — global base rate added to all ilks (currently 0 in most epochs)
rho    — timestamp of last drip() call for this ilk

Compounding formula:
  rate_new = rate_old × duty^(now - rho)

Anyone can call Jug.drip(ilk) to force an update (Keepers do this).

Annual fee from duty:
  annual_fee = (duty / RAY)^31_536_000 - 1

Example — 2% annual fee:
  duty per second = (1.02)^(1/31_536_000) ≈ 1.000000000627937
  as RAY integer  = 1000000000627937192491029810
```

---

## 6. Oracle System and OSM

### The Pipeline

```
14+ External price sources (independent oracle operators)
    │
    ▼
Median contract
    ├─ Takes the statistical median of all feeds
    └─ 1 bad oracle cannot move the price alone
    │
    ▼
OSM  (Oracle Security Module)   0x81FE72B5A8d1A857d176C3E7d5Bd2679A9B85763  [ETH]
    ├─ Stores: cur (current price, slot 3) and nxt (next price, slot 4)
    ├─ Introduces a 1-HOUR DELAY between Median update and Vat update
    └─ peek() is access-controlled; prices read via raw storage slots
    │
    ▼
Spot contract   0x65C79fcB50Ca1594B025960e539eD7A9a6D434A3
    ├─ Reads OSM cur price
    ├─ Divides by mat
    └─ Calls poke() to write ilk.spot into Vat
    │
    ▼
Vat   0x35D1b3F3D7966A1DFe207aa4514C12a259A0492B
    └─ All Vault safety checks use this delayed spot price
```

**Why the 1-hour delay?** It gives MKR governance time to react to an oracle attack. If a malicious operator pushes ETH price to $0, governance can call `osm.stop()` before the bad price propagates to the Vat. The delay is the system's primary defence against oracle manipulation.

### Live OSM Output (from `read_osm_price.py`)

```
OSM ETH-A:
  Current price : $2,298.28  (valid=True)
  Next price    : $2,298.28  (valid=True)
  Note: 'next' becomes 'current' after the next hourly poke()
```

**Reading OSM via storage slots** (because `peek()` is whitelisted on mainnet):
- Slot 3 → current price (`cur`): last 16 bytes = price (WAD), byte at index -17 = validity flag
- Slot 4 → next price (`nxt`): same layout
- Next price becomes current at the next hourly `poke()` call

---

## 7. Full Data Flow: Oracle → OSM → Spot → Vat → Urn

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PRICE ORACLE PIPELINE                       │
└─────────────────────────────────────────────────────────────────────┘

  [Oracle Feed 1] ──┐
  [Oracle Feed 2] ──┤
  [Oracle Feed 3] ──┼──► Median.poke()  ──► median = $2,298.28
       ...          │      (statistical median, 14+ sources)
  [Oracle Feed 14] ─┘

                                    │
                          1-hr delay applied
                                    │
                                    ▼

  ┌──────────────────────────────────────────┐
  │  OSM  (0x81FE...9B85763)                 │
  │  slot 3:  cur = $2,298.28  valid=True    │◄─ what Vat sees NOW
  │  slot 4:  nxt = $2,298.28  valid=True    │◄─ what Vat will see NEXT hour
  └──────────────────────────────────────────┘

                                    │
                          Spot.poke(ilk) called
                          reads OSM cur price
                                    │
                                    ▼

  ┌──────────────────────────────────────────────────────────────┐
  │  Spot  (0x65C7...4A3)                                        │
  │                                                              │
  │  ETH-A:  spot = $2,298.28 / 1.45 = $1,585.02  (RAY units)  │
  │  ETH-B:  spot = $2,298.28 / 1.30 = $1,767.91               │
  │  ETH-C:  spot = $2,298.28 / 1.70 = $1,351.93               │
  │  WBTC-A: separate OSM; spot = BTC_price / 1.50             │
  └──────────────────────────────────────────────────────────────┘

                                    │
                          Vat.file(ilk, "spot", value)
                                    │
                                    ▼

  ┌──────────────────────────────────────────────────────────────┐
  │  Vat  (0x35D1...492B) — core accounting ledger              │
  │                                                              │
  │  ilks["ETH-A"]:                                             │
  │    Art  = total normalised debt across all ETH-A urns        │
  │    rate = stability fee accumulator (grows via Jug.drip)     │
  │    spot = $1,585.02  ◄─ written by Spot.poke()             │
  │    line = debt ceiling                                       │
  │    dust = minimum debt                                       │
  └──────────────────────────────────────────────────────────────┘

                                    │
                        per-vault safety check
                        ink × spot  ≥  art × rate ?
                                    │
                          ┌─────────┴─────────┐
                          ▼                   ▼
              ┌─────────────────┐   ┌──────────────────────┐
              │  Urn (safe)     │   │  Urn (unsafe)        │
              │  ink: 2.0 ETH   │   │  ink × spot <        │
              │  art: 1,500 DAI │   │  art × rate          │
              │  ratio: 211%    │   │                       │
              └─────────────────┘   │  → Keeper calls       │
                                    │    Dog.bark(ilk, urn) │
                                    │  → Clipper auction    │
                                    └──────────────────────┘
```

---

## 8. Key Contract Addresses (Mainnet)

| Contract | Address |
|---|---|
| Vat | `0x35D1b3F3D7966A1DFe207aa4514C12a259A0492B` |
| Vow | `0xA950524441892A31ebddF91d3cEEFa04Bf454466` |
| Jug | `0x19c0976f590D67707E62397C87829d896Dc0f1F` ⚠️ verify checksum |
| Dog | `0x135954d155898D42C90D2a57824C690e0c7BEf1b` |
| Pot (DSR) | `0x197E90f9FAD81970bA7976f33CbD77088E5D7cf` |
| Spot | `0x65C79fcB50Ca1594B025960e539eD7A9a6D434A3` |
| OSM ETH-A | `0x81FE72B5A8d1A857d176C3E7d5Bd2679A9B85763` |
| OSM WBTC | `0xf185d0682d50819263941e5f4EacC763CC5C6C42` |
| Clipper ETH-A | `0xc67963a226eddd77B91aD8c421630A1b0AdFF270` |

> Canonical source: https://chainlog.makerdao.com — always verify here before using an address in prod.

---

## 9. Unit System Quick Reference

```
WAD = 10^18   token amounts (ink, art, MKR balances, DAI face values)
RAY = 10^27   rates and prices (rate, spot, duty, dsr, mat)
RAD = 10^45   DAI amounts inside Vat internal accounting (dai(addr), sin(addr), tab)

Conversions:
  actual_debt_DAI  = art × rate / RAY / WAD
  spot_in_dollars  = spot / RAY
  annual_fee       = (duty / RAY)^31_536_000 - 1
  unsafe_check     = ink × spot < art × rate   ← integer comparison, no division
```

---

## 10. TODO / Fix Before Week 42

- [ ] Fix `read_stability_fees.py` — Jug address checksum issue. Fetch canonical address from chainlog.makerdao.com and use `Web3.to_checksum_address()`.
- [ ] Run fixed script and paste actual `duty` values and `Last Drip` timestamps into section 5 above.
- [ ] Day 7 optional: run `read_vault.py` with a real vault owner from makerburn.com/#/vaults and paste output here.
