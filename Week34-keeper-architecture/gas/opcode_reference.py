# gas/opcode_reference.py
# Key gas costs post-EIP-2929 (Berlin hard fork)

OPCODE_COSTS = {
    "ADD": 3,
    "MUL": 5,
    "SLOAD_COLD": 2100,
    "SLOAD_WARM": 100,
    "SSTORE_NEW": 20000,
    "SSTORE_UPDATE": 2900,
    "SSTORE_REFUND_CLEAR": 4800,   # refund for zeroing a slot
    "CALL_COLD_ACCOUNT": 2600,
    "CALL_WARM_ACCOUNT": 100,
    "LOG0": 375,
    "LOG_PER_BYTE": 8,
    "SHA3_BASE": 30,
    "SHA3_WORD": 6,
    "CONTRACT_CREATE": 32000,
    "TX_BASE": 21000,
    "TX_CALLDATA_ZERO_BYTE": 4,
    "TX_CALLDATA_NONZERO_BYTE": 16,
}
