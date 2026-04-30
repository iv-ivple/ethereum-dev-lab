import asyncio
from web3 import AsyncWeb3, WebSocketProvider
from keeper.logging_config import setup_logging

logger = setup_logging()

class BlockListener:
    """
    Async WebSocket listener. Calls on_new_block(block_number) for every
    new block header received. Reconnects automatically on disconnect.
    """
    def __init__(self, ws_url: str, on_new_block):
        self.ws_url = ws_url
        self.on_new_block = on_new_block
        self._running = False

    async def start(self):
        self._running = True
        while self._running:
            try:
                async with AsyncWeb3(WebSocketProvider(self.ws_url)) as w3:
                    logger.info("WebSocket connected", extra={"state": "listening"})
                    subscription = await w3.eth.subscribe("newHeads")
                    async for block_header in subscription:
                        block_number = block_header["number"]
                        logger.info(f"New block: {block_number}")
                        await self.on_new_block(block_number)
            except Exception as e:
                logger.error(f"WebSocket error: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)

    def stop(self):
        self._running = False
