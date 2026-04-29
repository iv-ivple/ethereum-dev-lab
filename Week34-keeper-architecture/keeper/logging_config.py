import logging
import json
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        # Allow callers to attach extra structured fields
        for key in ("state", "tx_hash", "profit_eth", "opportunity_id"):
            if hasattr(record, key):
                log_record[key] = getattr(record, key)
        return json.dumps(log_record)

def setup_logging(level=logging.INFO, log_file="keeper.log"):
    handler_console = logging.StreamHandler()
    handler_file    = logging.FileHandler(log_file)
    formatter = JSONFormatter()
    for h in (handler_console, handler_file):
        h.setFormatter(formatter)
    logging.basicConfig(level=level, handlers=[handler_console, handler_file])
    return logging.getLogger("keeper")
