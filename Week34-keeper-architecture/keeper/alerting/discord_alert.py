import httpx
from keeper.config import config

async def send_discord_alert(message: str):
    if not config.discord_webhook_url:
        return
    async with httpx.AsyncClient() as client:
        try:
            await client.post(config.discord_webhook_url, json={"content": message}, timeout=5.0)
        except Exception as e:
            print(f"Discord alert failed: {e}")
