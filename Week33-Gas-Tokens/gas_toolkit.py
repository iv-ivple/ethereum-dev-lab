#!/usr/bin/env python3
# gas_toolkit.py — Week 31-33 Deliverable

import argparse
from gas.gas_oracle import get_gas_recommendation, get_network_congestion
from gas.eip1559_model import get_current_fees, simulate_base_fee_trajectory
from gas.tx_cost_estimator import get_eth_price_usd
from gas.fee_tracker import track_fees
from gas.tx_gas_profiler import profile_contract_gas
from gas.calldata_optimizer import count_calldata_cost

def cmd_status(args):
    """Show current network gas status."""
    congestion = get_network_congestion()
    fees = get_current_fees()
    eth_price = get_eth_price_usd()
    print(f"\n{'='*50}")
    print(f"  Network Congestion: {congestion.upper()}")
    print(f"  ETH Price:          ${eth_price:,.2f}" if eth_price else "  ETH Price: unavailable")
    print(f"  Base Fee:           {fees['base_fee_gwei']:.4f} Gwei")
    print(f"  Priority Fee:       {fees['priority_fee_gwei']:.4f} Gwei")
    print(f"  Max Fee:            {fees['max_fee_gwei']:.4f} Gwei")
    print(f"{'='*50}\n")
    print("Speed profiles:")
    for speed in ["slow", "standard", "fast", "instant"]:
        rec = get_gas_recommendation(speed)
        print(f"  {speed:8}: {rec['max_fee_gwei']:.4f} Gwei max")

def cmd_trajectory(args):
    """Show worst-case base fee trajectory."""
    traj = simulate_base_fee_trajectory(args.blocks)
    print(f"\nBase fee trajectory (worst case, {args.blocks} blocks):")
    for i, fee in enumerate(traj):
        bar = "█" * int(float(fee) / 2)
        print(f"  +{i} block(s): {fee:.3f} Gwei {bar}")

def cmd_calldata(args):
    """Analyze calldata cost for hex-encoded data."""
    result = count_calldata_cost(args.data)
    print(f"\nCalldata analysis for: {args.data[:20]}...")
    print(f"  Total bytes:    {result['total_bytes']}")
    print(f"  Zero bytes:     {result['zero_bytes']} × 4 gas = {result['zero_bytes']*4}")
    print(f"  Nonzero bytes:  {result['nonzero_bytes']} × 16 gas = {result['nonzero_bytes']*16}")
    print(f"  Total calldata gas: {result['calldata_gas']}")

def cmd_profile(args):
    """Profile gas usage for a contract address."""
    print(f"\nProfiling {args.address} over last {args.blocks} blocks...")
    stats = profile_contract_gas(args.address, args.blocks)
    for k, v in stats.items():
        print(f"  {k}: {v:,}" if isinstance(v, int) else f"  {k}: {v}")

def cmd_track(args):
    """Track base fee over time."""
    track_fees(
        duration_minutes=args.minutes,
        interval_seconds=args.interval,
        alert_threshold_gwei=args.alert
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gas Optimization Toolkit — Weeks 31-33")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("status", help="Current gas status and speed profiles")
    
    p_traj = sub.add_parser("trajectory", help="Worst-case base fee trajectory")
    p_traj.add_argument("--blocks", type=int, default=6)

    p_call = sub.add_parser("calldata", help="Analyze calldata gas cost")
    p_call.add_argument("data", help="Hex-encoded calldata (0x...)")

    p_prof = sub.add_parser("profile", help="Profile contract gas usage")
    p_prof.add_argument("address", help="Contract address")
    p_prof.add_argument("--blocks", type=int, default=1000)

    p_track = sub.add_parser("track", help="Track base fee over time")
    p_track.add_argument("--minutes", type=int, default=30)
    p_track.add_argument("--interval", type=int, default=15)
    p_track.add_argument("--alert", type=float, default=None, 
                         help="Alert when base fee drops below this Gwei value")

    args = parser.parse_args()
    cmds = {"status": cmd_status, "trajectory": cmd_trajectory,
            "calldata": cmd_calldata, "profile": cmd_profile, "track": cmd_track}
    
    if args.cmd in cmds:
        cmds[args.cmd](args)
    else:
        parser.print_help()
