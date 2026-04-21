#!/usr/bin/env python3
"""
arbitrage_simulator.py — CLI entry point for the DeFi Arbitrage Simulator.

Usage:
    python3 arbitrage_simulator.py --scan
    python3 arbitrage_simulator.py --run --interval 12
    python3 arbitrage_simulator.py --summary
    python3 arbitrage_simulator.py --optimize --triangle "WETH→USDC→DAI→WETH"
"""

import argparse
import sys
import time
import json
import os
from datetime import datetime

# ──────────────────────────────────────────────
# Module imports (all from root directory)
# ──────────────────────────────────────────────

def _import(module_name: str, friendly: str):
    """Try to import a module; print a warning and return None on failure."""
    try:
        import importlib
        return importlib.import_module(module_name)
    except ImportError as e:
        print(f"  [WARN] Could not import {friendly} ({module_name}): {e}")
        return None

# Lazy imports — only loaded when needed
_modules: dict = {}

def _get(name: str):
    if name not in _modules:
        mapping = {
            "scanner":          ("scanner",           "Scanner (single-scan logic)"),
            "main":             ("main",               "Main (continuous polling loop)"),
            "multi_hop_quote":  ("multi_hop_quote",   "Multi-hop quote (AMM simulation)"),
            "gas_calculator":   ("gas.advanced_gas_calculator", "Gas cost engine (advanced)"),
            "profit_engine":    ("profit_engine",     "Profit engine (net profit calc)"),
            "competition_model":("competition_model", "Competition model (MEV dynamics)"),
            "optimizer":        ("optimizer",         "Optimizer (optimal input size)"),
            "paper_trader":     ("paper_trader",      "Paper trader (logging & summary)"),
            "paths":            ("paths",             "Paths (triangle definitions)"),
        }
        mod, friendly = mapping[name]
        _modules[name] = _import(mod, friendly)
    return _modules[name]


# ──────────────────────────────────────────────
# PAPER_TRADES_FILE location
# ──────────────────────────────────────────────

PAPER_TRADES_FILE = os.environ.get("PAPER_TRADES_FILE", "paper_trades.json")


# ──────────────────────────────────────────────
# Command implementations
# ──────────────────────────────────────────────

def cmd_scan():
    """Run one scan pass and print all profitable opportunities."""
    print("\n" + "═" * 60)
    print("  ARBITRAGE SCAN  —  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("═" * 60)

    scanner = _get("scanner")
    paths_mod = _get("paths")
    gas_mod = _get("gas_calculator")
    profit_mod = _get("profit_engine")
    competition_mod = _get("competition_model")

    # Collect triangles
    triangles = []
    if paths_mod and hasattr(paths_mod, "get_triangles"):
        triangles = paths_mod.get_triangles()
    elif paths_mod and hasattr(paths_mod, "TRIANGLES"):
        triangles = paths_mod.TRIANGLES
    else:
        print("  [INFO] paths.py not available — using built-in default triangles.")
        triangles = [
            ["WETH", "USDC", "DAI"],
            ["WETH", "USDC", "USDT"],
            ["WETH", "DAI",  "USDT"],
        ]

    opportunities = []

    # Try scanner module first
    if scanner and hasattr(scanner, "scan"):
        print(f"  Scanning {len(triangles)} triangle(s) via scanner.scan() …\n")
        try:
            opportunities = scanner.scan(triangles)
        except Exception as e:
            print(f"  [ERROR] scanner.scan() failed: {e}")
    else:
        # Fallback: manual pipeline
        print(f"  Scanning {len(triangles)} triangle(s) manually …\n")
        for tri in triangles:
            label = "→".join(tri)
            try:
                # 1. Get AMM quote
                quote = None
                if _get("multi_hop_quote") and hasattr(_get("multi_hop_quote"), "get_quote"):
                    quote = _get("multi_hop_quote").get_quote(tri)

                # 2. Estimate gas (using advanced calculator)
                gas_cost = None
                gas_result = None
                GAS_UNITS_PER_ARB = 300_000  # typical triangle arb gas units
                if gas_mod and hasattr(gas_mod, "calculate_arb_gas_cost"):
                    gas_result = gas_mod.calculate_arb_gas_cost(
                        gas_units=GAS_UNITS_PER_ARB,
                        speed="fast",
                        verbose=False
                    )
                    gas_cost = gas_result.get("cost_usd") or gas_result.get("cost_eth")

                # 3. Calculate net profit
                net_profit = None
                if profit_mod and hasattr(profit_mod, "calculate_net_profit"):
                    net_profit = profit_mod.calculate_net_profit(quote, gas_cost)

                # 4. MEV competition check + congestion guard
                viable = True
                if gas_result and gas_result.get("congestion") == "very_high":
                    viable = False  # skip during extreme congestion
                elif competition_mod and hasattr(competition_mod, "is_viable"):
                    viable = competition_mod.is_viable(net_profit)

                opp = {
                    "triangle": label,
                    "quote": quote,
                    "gas_cost_usd": gas_cost,
                    "net_profit_usd": net_profit,
                    "viable": viable,
                }
                opportunities.append(opp)
            except Exception as e:
                print(f"  [ERROR] Triangle {label}: {e}")

    # Display results
    if not opportunities:
        print("  No opportunities found this scan.")
    else:
        profitable = [o for o in opportunities if o.get("net_profit_usd") and o["net_profit_usd"] > 0]
        print(f"  Found {len(opportunities)} path(s) | {len(profitable)} profitable\n")
        print(f"  {'Triangle':<30} {'Net Profit':>12}  {'Gas (USD)':>10}  {'Viable':>7}")
        print("  " + "─" * 65)
        for o in sorted(opportunities, key=lambda x: x.get("net_profit_usd") or 0, reverse=True):
            tri     = o.get("triangle", "?")
            profit  = o.get("net_profit_usd")
            gas     = o.get("gas_cost_usd")
            viable  = o.get("viable", "?")
            p_str   = f"${profit:>10.4f}" if isinstance(profit, (int, float)) else f"{'N/A':>11}"
            g_str   = f"${gas:>8.4f}"     if isinstance(gas,    (int, float)) else f"{'N/A':>9}"
            v_str   = "✓" if viable is True else ("✗" if viable is False else str(viable))
            print(f"  {tri:<30} {p_str}  {g_str}  {v_str:>7}")

    print("\n" + "═" * 60 + "\n")
    return opportunities


def cmd_run(interval: int):
    """Run continuously, logging paper trades, until interrupted."""
    print("\n" + "═" * 60)
    print(f"  CONTINUOUS MODE  —  interval: {interval}s")
    print("  Press Ctrl+C to stop.")
    print("═" * 60 + "\n")

    # Try main.py's loop first
    main_mod = _get("main")
    if main_mod and hasattr(main_mod, "run_loop"):
        try:
            main_mod.run_loop(interval=interval, trades_file=PAPER_TRADES_FILE)
            return
        except KeyboardInterrupt:
            print("\n  [STOP] Interrupted by user.")
            return
        except Exception as e:
            print(f"  [WARN] main.run_loop() failed ({e}). Falling back to built-in loop.")

    paper_trader = _get("paper_trader")
    iteration = 0

    try:
        while True:
            iteration += 1
            print(f"\n  ── Iteration #{iteration}  [{datetime.now().strftime('%H:%M:%S')}] ──")
            opportunities = cmd_scan()

            if paper_trader and hasattr(paper_trader, "log_trades"):
                try:
                    paper_trader.log_trades(opportunities, trades_file=PAPER_TRADES_FILE)
                    print(f"  [LOG] Trades appended to {PAPER_TRADES_FILE}")
                except Exception as e:
                    print(f"  [WARN] paper_trader.log_trades() failed: {e}")
                    _fallback_log(opportunities)
            else:
                _fallback_log(opportunities)

            print(f"\n  Sleeping {interval}s …")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n  [STOP] Continuous run ended by user.")


def _fallback_log(opportunities: list):
    """Write opportunities to paper_trades.json without paper_trader.py."""
    existing = []
    if os.path.exists(PAPER_TRADES_FILE):
        try:
            with open(PAPER_TRADES_FILE, "r") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = []

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "opportunities": opportunities,
    }
    existing.append(entry)

    with open(PAPER_TRADES_FILE, "w") as f:
        json.dump(existing, f, indent=2, default=str)
    print(f"  [LOG] Fallback-logged to {PAPER_TRADES_FILE}")


def cmd_summary():
    """Print a summary of all logged paper trades."""
    print("\n" + "═" * 60)
    print("  PAPER TRADE SUMMARY")
    print("═" * 60)

    paper_trader = _get("paper_trader")
    if paper_trader and hasattr(paper_trader, "summary"):
        try:
            paper_trader.summary(trades_file=PAPER_TRADES_FILE)
            print("═" * 60 + "\n")
            return
        except Exception as e:
            print(f"  [WARN] paper_trader.summary() failed: {e}. Using built-in summary.")

    # Built-in fallback summary
    if not os.path.exists(PAPER_TRADES_FILE):
        print(f"  No trade log found at '{PAPER_TRADES_FILE}'.")
        print("  Run with --run first to generate trades.\n")
        print("═" * 60 + "\n")
        return

    with open(PAPER_TRADES_FILE, "r") as f:
        log = json.load(f)

    total_scans = len(log)
    all_opps = [o for entry in log for o in entry.get("opportunities", [])]
    profitable = [o for o in all_opps if isinstance(o.get("net_profit_usd"), (int, float)) and o["net_profit_usd"] > 0]

    profits = [o["net_profit_usd"] for o in profitable]
    total_profit = sum(profits)
    best = max(profits) if profits else 0
    avg  = (total_profit / len(profits)) if profits else 0

    print(f"  Log file      : {PAPER_TRADES_FILE}")
    print(f"  Total scans   : {total_scans}")
    print(f"  Total paths   : {len(all_opps)}")
    print(f"  Profitable    : {len(profitable)}")
    print(f"  Total profit  : ${total_profit:.4f}")
    print(f"  Best single   : ${best:.4f}")
    print(f"  Avg profit    : ${avg:.4f}")

    if profitable:
        print("\n  Top 5 trades:")
        top5 = sorted(profitable, key=lambda x: x["net_profit_usd"], reverse=True)[:5]
        print(f"  {'Triangle':<30} {'Profit':>10}")
        print("  " + "─" * 42)
        for o in top5:
            print(f"  {o.get('triangle','?'):<30} ${o['net_profit_usd']:>8.4f}")

    print("\n" + "═" * 60 + "\n")


def cmd_optimize(triangle_str: str):
    """Find the optimal input size for a given triangle path."""
    print("\n" + "═" * 60)
    print(f"  OPTIMIZER  —  {triangle_str}")
    print("═" * 60)

    # Parse triangle string (supports → or -> or comma)
    for sep in ["→", "->", ","]:
        if sep in triangle_str:
            tokens = [t.strip() for t in triangle_str.split(sep)]
            break
    else:
        tokens = [triangle_str.strip()]

    print(f"  Tokens : {' → '.join(tokens)}\n")

    optimizer = _get("optimizer")
    if optimizer and hasattr(optimizer, "find_optimal_input"):
        try:
            result = optimizer.find_optimal_input(tokens)
            print(f"  Result : {result}")
        except Exception as e:
            print(f"  [ERROR] optimizer.find_optimal_input() failed: {e}")
            _fallback_optimize(tokens)
    else:
        _fallback_optimize(tokens)

    print("\n" + "═" * 60 + "\n")


def _fallback_optimize(tokens: list):
    """Simple brute-force sweep across input sizes."""
    print("  [INFO] Running built-in sweep optimizer …\n")
    multi_hop = _get("multi_hop_quote")
    gas_mod   = _get("gas_calculator")
    profit_mod = _get("profit_engine")

    best_input  = None
    best_profit = None

    candidates = [0.1, 0.5, 1, 2, 5, 10, 20, 50, 100, 500, 1000]
    print(f"  {'Input (ETH)':>12}  {'Net Profit (USD)':>18}")
    print("  " + "─" * 34)

    for amt in candidates:
        try:
            quote  = multi_hop.get_quote(tokens, input_amount=amt) if multi_hop and hasattr(multi_hop, "get_quote") else None
            gas    = gas_mod.estimate_gas(tokens)                   if gas_mod   and hasattr(gas_mod,   "estimate_gas") else None
            profit = profit_mod.calculate_net_profit(quote, gas)    if profit_mod and hasattr(profit_mod, "calculate_net_profit") else None
        except Exception:
            profit = None

        p_str = f"${profit:.4f}" if isinstance(profit, (int, float)) else "N/A"
        print(f"  {amt:>12}  {p_str:>18}")

        if isinstance(profit, (int, float)):
            if best_profit is None or profit > best_profit:
                best_profit = profit
                best_input  = amt

    print()
    if best_input is not None:
        print(f"  ★ Optimal input : {best_input} ETH  →  profit ${best_profit:.4f}")
    else:
        print("  Could not determine optimal input (modules unavailable or no profitable size found).")


# ──────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arbitrage_simulator.py",
        description="DeFi Arbitrage Simulator — Week 28-30 CLI Deliverable",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 arbitrage_simulator.py --scan
  python3 arbitrage_simulator.py --run --interval 12
  python3 arbitrage_simulator.py --summary
  python3 arbitrage_simulator.py --optimize --triangle "WETH→USDC→DAI→WETH"
        """,
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--scan",     action="store_true", help="Run one scan and print all opportunities")
    mode.add_argument("--run",      action="store_true", help="Run continuously and log paper trades")
    mode.add_argument("--summary",  action="store_true", help="Show summary of logged paper trades")
    mode.add_argument("--optimize", action="store_true", help="Find optimal input size for a triangle")

    parser.add_argument(
        "--interval", type=int, default=12, metavar="SECONDS",
        help="Polling interval in seconds for --run mode (default: 12)"
    )
    parser.add_argument(
        "--triangle", type=str, metavar="PATH",
        help='Triangle path for --optimize, e.g. "WETH→USDC→DAI→WETH"'
    )
    parser.add_argument(
        "--trades-file", type=str, default=PAPER_TRADES_FILE, metavar="FILE",
        help=f"Path to paper trades JSON log (default: {PAPER_TRADES_FILE})"
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Honour custom trades file
    global PAPER_TRADES_FILE
    PAPER_TRADES_FILE = args.trades_file

    if args.scan:
        cmd_scan()

    elif args.run:
        cmd_run(interval=args.interval)

    elif args.summary:
        cmd_summary()

    elif args.optimize:
        if not args.triangle:
            parser.error("--optimize requires --triangle, e.g. --triangle \"WETH→USDC→DAI→WETH\"")
        cmd_optimize(args.triangle)


if __name__ == "__main__":
    main()
