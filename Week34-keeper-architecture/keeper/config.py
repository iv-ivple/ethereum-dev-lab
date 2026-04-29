import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class KeeperConfig:
    # Network
    rpc_http_url: str = os.getenv("RPC_HTTP_URL", "")
    rpc_ws_url: str   = os.getenv("RPC_WS_URL", "")

    # Wallet
    keeper_address: str  = os.getenv("KEEPER_ADDRESS", "")
    private_key: str     = os.getenv("PRIVATE_KEY", "")

    # Strategy thresholds
    min_profit_eth: float  = float(os.getenv("MIN_PROFIT_ETH", "0.002"))
    max_gas_gwei: float    = float(os.getenv("MAX_GAS_GWEI", "50"))
    slippage_bps: int      = int(os.getenv("SLIPPAGE_BPS", "50"))    # 0.5%

    # Execution safety
    max_consecutive_failures: int = int(os.getenv("MAX_FAILURES", "5"))
    cooldown_seconds: int         = int(os.getenv("COOLDOWN_SECONDS", "30"))
    tx_confirm_timeout_blocks: int = int(os.getenv("CONFIRM_TIMEOUT_BLOCKS", "3"))

    # Alerting
    telegram_bot_token: str  = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str    = os.getenv("TELEGRAM_CHAT_ID", "")
    discord_webhook_url: str = os.getenv("DISCORD_WEBHOOK_URL", "")

    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///keeper.db")

    def validate(self):
        assert self.rpc_http_url, "RPC_HTTP_URL is required"
        assert self.rpc_ws_url,   "RPC_WS_URL is required"
        assert self.keeper_address, "KEEPER_ADDRESS is required"
        assert self.private_key,  "PRIVATE_KEY is required"

config = KeeperConfig()
