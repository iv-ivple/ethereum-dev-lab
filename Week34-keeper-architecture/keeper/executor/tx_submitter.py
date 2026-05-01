import asyncio
from web3 import Web3
from keeper.logging_config import setup_logging

logger = setup_logging()

async def submit_and_confirm(raw_tx: str, w3: Web3, timeout_blocks: int = 3) -> dict:
    """
    Submit raw_tx, then poll for a receipt.
    Returns the receipt dict on success.
    Raises TimeoutError if not confirmed within timeout_blocks.
    """
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    logger.info(f"Transaction submitted", extra={"tx_hash": tx_hash.hex()})

    start_block = w3.eth.block_number
    while True:
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                if receipt["status"] == 1:
                    logger.info("Transaction confirmed", extra={
                        "tx_hash": tx_hash.hex(),
                        "gas_used": receipt["gasUsed"],
                        "block": receipt["blockNumber"],
                    })
                    return receipt
                else:
                    raise RuntimeError(f"Transaction reverted: {tx_hash.hex()}")
        except Exception as e:
            if "reverted" in str(e):
                raise

        current_block = w3.eth.block_number
        if current_block > start_block + timeout_blocks:
            raise TimeoutError(f"Tx {tx_hash.hex()} not confirmed after {timeout_blocks} blocks")
        await asyncio.sleep(2)
