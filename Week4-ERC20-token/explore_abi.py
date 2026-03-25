#!/usr/bin/env python3
"""
Explore how ABIs work with ERC-20 tokens
"""
import json
from web3 import Web3

# Minimal ERC-20 ABI (just the essential functions)
ERC20_ABI = json.loads('''
[
    {
        "constant": true,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]
''')

def explain_abi():
    """Explain each part of the ABI"""
    print("=" * 60)
    print("UNDERSTANDING ERC-20 ABI")
    print("=" * 60)
    
    for i, function in enumerate(ERC20_ABI, 1):
        print(f"\n{i}. Function: {function['name']}")
        print(f"   Type: {function['type']}")
        print(f"   Constant (read-only): {function.get('constant', False)}")
        
        if function['inputs']:
            print(f"   Inputs:")
            for inp in function['inputs']:
                print(f"     - {inp['name']}: {inp['type']}")
        else:
            print(f"   Inputs: None")
        
        print(f"   Outputs:")
        for out in function['outputs']:
            name = out['name'] if out['name'] else '(unnamed)'
            print(f"     - {name}: {out['type']}")

def demonstrate_function_selector():
    """Show how function selectors work"""
    print("\n" + "=" * 60)
    print("FUNCTION SELECTORS")
    print("=" * 60)
    print("\nFunction selectors are the first 4 bytes of the")
    print("Keccak-256 hash of the function signature.\n")
    
    w3 = Web3()
    
    functions = [
        "name()",
        "symbol()",
        "decimals()",
        "balanceOf(address)",
        "totalSupply()"
    ]
    
    for func_sig in functions:
        # Calculate function selector
        selector = w3.keccak(text=func_sig)[:4].hex()
        print(f"{func_sig:25} => {selector}")

if __name__ == "__main__":
    explain_abi()
    demonstrate_function_selector()
    
    print("\n" + "=" * 60)
    print("KEY TAKEAWAYS")
    print("=" * 60)
    print("1. ABI defines how to interact with smart contracts")
    print("2. Function selectors identify which function to call")
    print("3. 'constant' or 'view' functions don't modify blockchain state")
    print("4. Type information ensures correct encoding/decoding")
