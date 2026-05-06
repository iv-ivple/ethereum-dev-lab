from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Connection strings
    rpc_url: str
    database_url: str
    discord_webhook_url: str

    # Alert thresholds
    health_factor_warning: float = 1.5
    health_factor_critical: float = 1.1

    # Polling
    poll_interval_seconds: int = 60

    # Seed wallets (comma-separated string in .env → list of strings)
    seed_wallets: List[str] = []

    @field_validator("seed_wallets", mode="before")
    @classmethod
    def parse_seed_wallets(cls, v):
        if isinstance(v, str):
            return [w.strip().lower() for w in v.split(",") if w.strip()]
        return v

    # Aave V3 on Sepolia
    # Always verify at: https://docs.aave.com/developers/deployed-contracts/v3-testnet-addresses
    aave_pool_addresses_provider: str = "0x012bAC54348C0E635dCAc9D5FB99f06F24136C9A"


# Single shared instance imported everywhere
config = Config()
