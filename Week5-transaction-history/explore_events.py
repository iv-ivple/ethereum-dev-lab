"""
Ethereum Event Explorer - Understanding ERC-20 Transfer Events

This script demonstrates how Ethereum events work, focusing on the ERC-20 Transfer event.
It covers event structures, topics vs data, and event signature calculation.
"""

from web3 import Web3
from eth_utils import keccak, to_hex

def calculate_event_signature(event_string):
    """
    Calculate the keccak256 hash of an event signature string.
    
    Event signatures are calculated by:
    1. Taking the event name and parameter types (no spaces, no parameter names)
    2. Computing keccak256 hash of this string
    3. The resulting hash becomes Topic[0] in the event log
    
    Args:
        event_string: Event signature like "Transfer(address,address,uint256)"
    
    Returns:
        Hexadecimal string of the keccak256 hash
    """
    signature_hash = keccak(text=event_string)
    return to_hex(signature_hash)

def explain_erc20_transfer_event():
    """
    Explain the structure of an ERC-20 Transfer event and demonstrate
    how topics and data work in Ethereum events.
    """
    print("=" * 80)
    print("ERC-20 TRANSFER EVENT STRUCTURE")
    print("=" * 80)
    print()
    
    # The ERC-20 Transfer event definition
    print("Event Definition in Solidity:")
    print("-" * 80)
    print("event Transfer(address indexed from, address indexed to, uint256 value);")
    print()
    
    # Calculate the event signature
    event_string = "Transfer(address,address,uint256)"
    signature = calculate_event_signature(event_string)
    
    print("Event Signature Calculation:")
    print("-" * 80)
    print(f"Input String: {event_string}")
    print(f"Keccak256 Hash: {signature}")
    print()
    
    # Verify it matches the known Transfer event signature
    expected_signature = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    print(f"Expected Signature: {expected_signature}")
    print(f"Match: {signature == expected_signature}")
    print()
    
    # Explain Topics vs Data
    print("=" * 80)
    print("TOPICS VS DATA IN EVENTS")
    print("=" * 80)
    print()
    
    print("TOPICS (Indexed Parameters):")
    print("-" * 80)
    print("• Topics are indexed and can be efficiently filtered/searched")
    print("• Maximum of 3 indexed parameters per event (4 topics total)")
    print("• Topic[0] is ALWAYS the event signature hash")
    print("• Topic[1], Topic[2], Topic[3] contain indexed parameter values")
    print("• For the Transfer event:")
    print("  - Topic[0] = Event signature (keccak256 hash)")
    print("  - Topic[1] = 'from' address (indexed)")
    print("  - Topic[2] = 'to' address (indexed)")
    print()
    
    print("DATA (Non-Indexed Parameters):")
    print("-" * 80)
    print("• Data contains non-indexed parameters")
    print("• Cannot be filtered directly (must retrieve and decode)")
    print("• More gas-efficient to store than indexed parameters")
    print("• For the Transfer event:")
    print("  - Data = 'value' (uint256 amount transferred)")
    print()
    
    # Example event log structure
    print("=" * 80)
    print("EXAMPLE TRANSFER EVENT LOG STRUCTURE")
    print("=" * 80)
    print()
    
    example_from = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
    example_to = "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
    example_value = "1000000000000000000"  # 1 token (with 18 decimals)
    
    print("Example Transfer:")
    print(f"  From: {example_from}")
    print(f"  To: {example_to}")
    print(f"  Value: {example_value} (1 token with 18 decimals)")
    print()
    
    # Pad addresses to 32 bytes (Ethereum uses 32-byte words)
    from_padded = Web3.to_bytes(hexstr=example_from).rjust(32, b'\x00')
    to_padded = Web3.to_bytes(hexstr=example_to).rjust(32, b'\x00')
    
    print("Resulting Event Log:")
    print("-" * 80)
    print(f"topics[0]: {signature}")
    print(f"           ^ Event signature")
    print()
    print(f"topics[1]: {Web3.to_hex(from_padded)}")
    print(f"           ^ 'from' address (padded to 32 bytes)")
    print()
    print(f"topics[2]: {Web3.to_hex(to_padded)}")
    print(f"           ^ 'to' address (padded to 32 bytes)")
    print()
    print(f"data:      {Web3.to_hex(int(example_value).to_bytes(32, byteorder='big'))}")
    print(f"           ^ 'value' amount (32 bytes)")
    print()

def demonstrate_event_filtering():
    """
    Demonstrate how indexed parameters (topics) enable efficient event filtering.
    """
    print("=" * 80)
    print("WHY USE INDEXED PARAMETERS?")
    print("=" * 80)
    print()
    
    print("Indexed parameters allow efficient filtering when querying events:")
    print()
    print("Example Queries:")
    print("-" * 80)
    print("1. Find all transfers FROM a specific address:")
    print("   - Filter by Topic[1] (from address)")
    print()
    print("2. Find all transfers TO a specific address:")
    print("   - Filter by Topic[2] (to address)")
    print()
    print("3. Find all transfers between two specific addresses:")
    print("   - Filter by both Topic[1] AND Topic[2]")
    print()
    print("4. Find transfers of a specific amount:")
    print("   - CANNOT filter directly (amount is in data, not indexed)")
    print("   - Must retrieve all events and decode data to find matches")
    print()

def additional_examples():
    """
    Show event signatures for other common Ethereum events.
    """
    print("=" * 80)
    print("OTHER COMMON EVENT SIGNATURES")
    print("=" * 80)
    print()
    
    events = [
        "Approval(address,address,uint256)",
        "Deposit(address,uint256)",
        "Withdrawal(address,uint256)",
        "Swap(address,uint256,uint256,uint256,uint256,address)",
    ]
    
    for event in events:
        sig = calculate_event_signature(event)
        print(f"{event}")
        print(f"  → {sig}")
        print()

def main():
    """
    Main function to run all demonstrations.
    """
    print()
    explain_erc20_transfer_event()
    print()
    demonstrate_event_filtering()
    print()
    additional_examples()
    
    print("=" * 80)
    print("KEY TAKEAWAYS")
    print("=" * 80)
    print()
    print("1. Event signatures are keccak256 hashes of 'EventName(type1,type2,...)'")
    print("2. Topic[0] always contains the event signature")
    print("3. Indexed parameters (max 3) go in Topic[1], Topic[2], Topic[3]")
    print("4. Non-indexed parameters go in the data field")
    print("5. Indexed parameters enable efficient filtering and searching")
    print("6. Non-indexed parameters are more gas-efficient but not filterable")
    print()

if __name__ == "__main__":
    main()
