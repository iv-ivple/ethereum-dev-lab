"""
Simple CLI for managing monitored wallets.

Usage:
    python -m src.cli add <address> [label]
    python -m src.cli list
    python -m src.cli deactivate <address>
"""
import asyncio
import sys
from src.db import init_db, close_db, upsert_wallet, get_active_wallets, get_pool


async def cmd_add(address: str, label: str | None):
    await init_db()
    wallet = await upsert_wallet(address, label)
    print(f"✅ Added: {wallet['address']}  ({wallet['label'] or 'no label'})")
    await close_db()


async def cmd_list():
    await init_db()
    wallets = await get_active_wallets()
    if not wallets:
        print("No active wallets.")
    for w in wallets:
        print(f"  {w['address']}  {w['label'] or ''}")
    await close_db()


async def cmd_deactivate(address: str):
    await init_db()
    await get_pool().execute(
        "UPDATE wallets SET active = FALSE WHERE address = $1", address.lower()
    )
    print(f"⏸  Deactivated: {address}")
    await close_db()


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    command = args[0]
    if command == "add" and len(args) >= 2:
        label = args[2] if len(args) > 2 else None
        asyncio.run(cmd_add(args[1], label))
    elif command == "list":
        asyncio.run(cmd_list())
    elif command == "deactivate" and len(args) == 2:
        asyncio.run(cmd_deactivate(args[1]))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
