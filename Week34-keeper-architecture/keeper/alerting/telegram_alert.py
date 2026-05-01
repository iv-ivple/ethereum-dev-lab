import httpx
from keeper.config import config

async def send_alert(message: str):
    """Send a message to the configured Telegram chat."""
    if not config.telegram_bot_token or not config.telegram_chat_id:
        return
    url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
    payload = {"chat_id": config.telegram_chat_id, "text": message, "parse_mode": "HTML"}
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json=payload, timeout=5.0)
        except Exception as e:
            # Alerting failures must never crash the keeper
            print(f"Alert failed: {e}")
