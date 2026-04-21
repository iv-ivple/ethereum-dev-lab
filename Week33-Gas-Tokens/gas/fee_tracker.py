# gas/fee_tracker.py
from web3 import Web3
import os, time, json
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))

def track_fees(
    duration_minutes: int = 30,
    interval_seconds: int = 15,
    alert_threshold_gwei: float = None
):
    """
    Poll base fee every interval_seconds for duration_minutes.
    Logs results to gas/fee_history_log.json.
    Optionally alerts when base fee drops below alert_threshold_gwei.
    """
    log_path = os.path.join(os.path.dirname(__file__), "fee_history_log.json")
    total_seconds = duration_minutes * 60
    elapsed = 0
    records = []

    print(f"Tracking fees for {duration_minutes} min (every {interval_seconds}s). Ctrl+C to stop.")
    if alert_threshold_gwei:
        print(f"Alert threshold: {alert_threshold_gwei} Gwei\n")

    try:
        while elapsed <= total_seconds:
            block = w3.eth.get_block("latest")
            base_fee_wei = block.get("baseFeePerGas", 0)
            base_fee_gwei = round(float(Web3.from_wei(base_fee_wei, "gwei")), 4)
            timestamp = int(time.time())

            record = {
                "timestamp": timestamp,
                "block": block["number"],
                "base_fee_gwei": base_fee_gwei,
            }
            records.append(record)

            alert = ""
            if alert_threshold_gwei and base_fee_gwei < alert_threshold_gwei:
                alert = f"  *** ALERT: below {alert_threshold_gwei} Gwei! ***"

            print(f"[{time.strftime('%H:%M:%S')}] Block {block['number']} | "
                  f"Base fee: {base_fee_gwei:.4f} Gwei{alert}")

            time.sleep(interval_seconds)
            elapsed += interval_seconds

    except KeyboardInterrupt:
        print("\nStopped early.")

    # Save log
    with open(log_path, "w") as f:
        json.dump(records, f, indent=2)

    print(f"\nDone. {len(records)} records saved to {log_path}")

    # Summary
    if records:
        fees = [r["base_fee_gwei"] for r in records]
        print(f"Min: {min(fees):.4f} Gwei | Max: {max(fees):.4f} Gwei | "
              f"Avg: {sum(fees)/len(fees):.4f} Gwei")
