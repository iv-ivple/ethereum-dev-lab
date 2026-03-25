# paper_trader.py

import json
import os
from datetime import datetime, timezone
from profit_engine import ArbitrageOpportunity
from decimal import Decimal

LOG_FILE = "paper_trades.json"

def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def log_opportunity(opp: ArbitrageOpportunity, block_number: int):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "block": block_number,
        "name": opp.name,
        "input_eth": opp.input_eth,
        "gross_profit_eth": opp.gross_profit_eth,
        "gas_cost_eth": opp.gas_cost_eth,
        "net_profit_eth": opp.net_profit_eth,
        "net_profit_usd": opp.net_profit_usd,
        "roi_percent": opp.roi_percent,
        "profitable": opp.profitable,
    }

    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)

    logs.append(entry)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2, default=decimal_to_float)

def get_summary() -> dict:
    if not os.path.exists(LOG_FILE):
        return {}
    with open(LOG_FILE) as f:
        try:
            logs = json.load(f)
        except json.JSONDecodeError:
            logs = []
    
    profitable = [l for l in logs if l["profitable"]]
    return {
        "total_scans": len(logs),
        "profitable_opportunities": len(profitable),
        "hit_rate_percent": len(profitable) / len(logs) * 100 if logs else 0,
        "total_simulated_profit_eth": sum(l["net_profit_eth"] for l in profitable),
        "avg_net_profit_eth": sum(l["net_profit_eth"] for l in profitable) / len(profitable) if profitable else 0,
    }
