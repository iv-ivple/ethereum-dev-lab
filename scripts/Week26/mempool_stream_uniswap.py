import asyncio
import json
import os
from web3 import Web3, AsyncWeb3
from web3.providers import WebSocketProvider
from dotenv import load_dotenv

load_dotenv()
WSS_URL = os.getenv("WSS_URL")
RPC_URL = os.getenv("RPC_URL")

UNISWAP_V2_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D".lower()
MIN_VALUE_ETH = 1.0

# --- ABI setup (sync web3 instance used only for decoding) ---
with open('abis/uniswap_v2_router.json') as f:
    ROUTER_ABI = json.load(f)

w3_sync = Web3(Web3.HTTPProvider(RPC_URL))
router_contract = w3_sync.eth.contract(
    address=Web3.to_checksum_address(UNISWAP_V2_ROUTER),
    abi=ROUTER_ABI
)

def decode_swap(input_data):
    """Decode raw transaction input into function name and parameters."""
    try:
        func, params = router_contract.decode_function_input(input_data)
        return func.fn_name, params
    except Exception:
        return None, None

# --- Async mempool streaming ---
async def handle_pending_tx(w3, tx_hash):
    """Fetch transaction, filter for large Uniswap swaps, and decode input."""
    try:
        tx = await w3.eth.get_transaction(tx_hash)
        if tx and tx.to:
            target = tx.to.lower()
            value_eth = float(w3.from_wei(tx.value, 'ether'))

            if target == UNISWAP_V2_ROUTER and value_eth >= MIN_VALUE_ETH:
                gas_price = getattr(tx, 'maxFeePerGas', None) or getattr(tx, 'gasPrice', 0)
                gas_gwei = w3.from_wei(gas_price, 'gwei')

                print(f"🎯 LARGE UNISWAP TX DETECTED")
                print(f"   Hash:  {tx_hash.hex()}")
                print(f"   Value: {value_eth:.4f} ETH")
                print(f"   Gas:   {gas_gwei:.2f} Gwei")

                # Decode the swap function and parameters
                fn_name, params = decode_swap(tx.input)
                if fn_name:
                    print(f"   Function: {fn_name}")
                    if params and 'path' in params:
                        path_str = ' → '.join(params['path'])
                        print(f"   Path:     {path_str}")
                    if params and 'amountOutMin' in params:
                        print(f"   Min Out:  {params['amountOutMin']}")
                    if params and 'amountIn' in params:
                        print(f"   Amount In:{params['amountIn']}")
                else:
                    # Fallback: show raw input prefix if decoding fails
                    print(f"   Input: {tx.input.hex()[:20]}... (unknown function)")
                print()
    except Exception:
        pass  # tx may have been confirmed already

async def stream_mempool():
    async with AsyncWeb3(WebSocketProvider(WSS_URL)) as w3:
        print(f"Connected. Watching for Uniswap V2 txs > {MIN_VALUE_ETH} ETH...")
        print(f"Router: {UNISWAP_V2_ROUTER}")
        print()
        subscription_id = await w3.eth.subscribe("newPendingTransactions")

        count = 0
        async for payload in w3.socket.process_subscriptions():
            tx_hash = payload["result"]
            await handle_pending_tx(w3, tx_hash)
            count += 1
            if count >= 2000:
                break

        await w3.eth.unsubscribe(subscription_id)
        print("Done.")

asyncio.run(stream_mempool())

