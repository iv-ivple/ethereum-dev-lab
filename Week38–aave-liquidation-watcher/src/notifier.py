import aiohttp
from datetime import datetime, timezone
from src.config import config

# Discord embed colours
COLORS = {
    "INFO":     0x5865F2,   # Discord blurple
    "WARNING":  0xFFA500,   # Orange
    "CRITICAL": 0xFF0000,   # Red
}


def _fmt_hf(hf: float) -> str:
    return "∞" if hf == float("inf") else f"{hf:.4f}"


async def send_alert(
    alert_type: str,
    wallet_address: str,
    position: dict,
    simulation: dict | None = None,
) -> None:
    """Send a rich Discord embed for a WARNING or CRITICAL health factor."""
    is_critical = alert_type == "CRITICAL"
    threshold = config.health_factor_critical if is_critical else config.health_factor_warning

    fields = [
        {"name": "🏦 Wallet",         "value": f"`{wallet_address}`",                        "inline": False},
        {"name": "❤️ Health Factor",   "value": f"**{_fmt_hf(position['health_factor'])}** (threshold: {threshold})", "inline": True},
        {"name": "💰 Collateral",      "value": f"${position['total_collateral_usd']:.2f}",   "inline": True},
        {"name": "📉 Debt",            "value": f"${position['total_debt_usd']:.2f}",         "inline": True},
        {
            "name":   "📊 LTV / Liq. Threshold",
            "value":  f"{position['ltv']:.1f}% / {position['liquidation_threshold']:.1f}%",
            "inline": True,
        },
    ]

    if simulation:
        fields.append({
            "name": "🤖 Simulated Liquidation Opportunity",
            "value": (
                f"Debt to repay: **${simulation['debt_to_repay']:.2f}**\n"
                f"Collateral received: **${simulation['collateral_gain']:.2f}**\n"
                f"Estimated profit: **${simulation['profit']:.2f}**\n"
                f"*(Simulation only — not executed)*"
            ),
            "inline": False,
        })

    payload = {
        "username":   "Aave Liquidation Watcher",
        "avatar_url": "https://cryptologos.cc/logos/aave-aave-logo.png",
        "embeds": [{
            "title":       "🚨 CRITICAL — Liquidation Imminent!" if is_critical else "⚠️ WARNING — Low Health Factor",
            "description": "Position at risk on **Aave V3 Sepolia**",
            "color":       COLORS[alert_type],
            "fields":      fields,
            "footer":      {"text": "Aave Liquidation Watcher • Simulation only — no trades executed"},
            "timestamp":   datetime.now(timezone.utc).isoformat(),
        }],
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(config.discord_webhook_url, json=payload) as resp:
            if resp.status not in (200, 204):
                text = await resp.text()
                raise RuntimeError(f"Discord webhook failed {resp.status}: {text}")


async def send_heartbeat(wallets_count: int, snapshots_saved: int) -> None:
    """Hourly ping to Discord confirming the bot is still alive."""
    payload = {
        "username": "Aave Liquidation Watcher",
        "embeds": [{
            "title": "💓 Heartbeat",
            "color": COLORS["INFO"],
            "fields": [
                {"name": "Wallets Monitored", "value": str(wallets_count),  "inline": True},
                {"name": "Snapshots Saved",   "value": str(snapshots_saved), "inline": True},
                {"name": "Last Poll",         "value": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "inline": True},
            ],
            "footer":    {"text": "Aave Liquidation Watcher"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }],
    }
    async with aiohttp.ClientSession() as session:
        await session.post(config.discord_webhook_url, json=payload)
