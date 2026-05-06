# gas/calldata_optimizer.py

def count_calldata_cost(hex_data: str) -> dict:
    """
    Calculate the calldata gas cost for a hex-encoded transaction input.
    EIP-2028 costs: zero byte = 4 gas, non-zero byte = 16 gas.
    """
    if hex_data.startswith("0x"):
        hex_data = hex_data[2:]
    
    bytes_data = bytes.fromhex(hex_data)
    zero_bytes = sum(1 for b in bytes_data if b == 0)
    nonzero_bytes = len(bytes_data) - zero_bytes
    
    cost = (zero_bytes * 4) + (nonzero_bytes * 16)
    return {
        "total_bytes": len(bytes_data),
        "zero_bytes": zero_bytes,
        "nonzero_bytes": nonzero_bytes,
        "calldata_gas": cost,
    }

def optimize_uint_encoding(value: int) -> str:
    """
    Demonstrates why packing small uints into fewer slots saves gas.
    ABI encoding always pads to 32 bytes — choose types wisely in Solidity.
    """
    from eth_abi import encode
    packed = encode(["uint256"], [value]).hex()
    zero_count = packed.count("00") // 2  # approximate leading zeros
    return f"0x{packed} — {zero_count} leading zero bytes (cheap calldata)"
