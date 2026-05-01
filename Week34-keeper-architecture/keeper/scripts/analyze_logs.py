import json, sys
from collections import Counter
from pathlib import Path

log_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("keeper.log")
lines = [json.loads(l) for l in log_file.read_text().splitlines() if l.strip()]

states       = Counter(l.get("state") for l in lines if l.get("state"))
errors       = [l for l in lines if l["level"] == "ERROR"]
successes    = [l for l in lines if "profit_eth" in l]
total_profit = sum(l["profit_eth"] for l in successes)

print(f"State distribution: {dict(states)}")
print(f"Total errors: {len(errors)}")
print(f"Total successes: {len(successes)}")
print(f"Total profit logged: {total_profit:.5f} ETH")
