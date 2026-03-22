import asyncio
import os
from web3 import AsyncWeb3
from web3.providers import WebSocketProvider
from dotenv import load_dotenv

load_dotenv()
WSS_URL = os.getenv("WSS_URL")

async def handle_pending_tx(w3, tx_hash):
    """Fetch and print details of a pending transaction."""
    try:
        tx = await w3.eth.get_transaction(tx_hash)
        if tx and tx.to:
            value_eth = w3.from_wei(tx.value, 'ether')
            # web3.py v7: EIP-1559 txs use maxFeePerGas, legacy use gasPrice
            gas_price = getattr(tx, 'maxFeePerGas', None) or getattr(tx, 'gasPrice', 0)
            gas_gwei = w3.from_wei(gas_price, 'gwei')
            print(f"[PENDING] {tx_hash.hex()[:16]}... | "
                  f"To: {tx.to[:10]}... | "
                  f"Value: {value_eth:.4f} ETH | "
                  f"Gas: {gas_gwei:.1f} Gwei")
    except Exception:
        pass  # tx may have been confirmed already

async def stream_mempool():
    async with AsyncWeb3(WebSocketProvider(WSS_URL)) as w3:
        print("Connected. Streaming pending transactions...")
        subscription_id = await w3.eth.subscribe("newPendingTransactions")

        count = 0
        async for payload in w3.socket.process_subscriptions():
            tx_hash = payload["result"]
            await handle_pending_tx(w3, tx_hash)
            count += 1
            if count >= 50:  # stop after 50 transactions
                break

        await w3.eth.unsubscribe(subscription_id)
        print("Done.")

asyncio.run(stream_mempool())

