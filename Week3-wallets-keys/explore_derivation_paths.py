#!/usr/bin/env python3
"""
Explore different BIP44 derivation paths for Ethereum.
Shows how different paths create different addresses from the same seed.
"""

from eth_account import Account
Account.enable_unaudited_hdwallet_features()

# Test mnemonic (NEVER use this for real funds!)
TEST_MNEMONIC = "test test test test test test test test test test test junk"

def derive_with_path(mnemonic, path):
    """Derive account using custom path."""
    account = Account.from_mnemonic(mnemonic, account_path=path)
    return account.address

def main():
    print("=" * 70)
    print("DERIVATION PATH EXPLORER")
    print("=" * 70)
    print(f"\nUsing test mnemonic: {TEST_MNEMONIC}")
    print()
    
    # Different derivation paths
    paths = [
        ("m/44'/60'/0'/0/0", "Standard Ethereum (MetaMask default)"),
        ("m/44'/60'/0'/0/1", "Standard Ethereum (Account 1)"),
        ("m/44'/60'/0'/0/2", "Standard Ethereum (Account 2)"),
        ("m/44'/60'/1'/0/0", "Different account branch"),
        ("m/44'/60'/0'/1/0", "Internal chain (change addresses)"),
    ]
    
    print("📍 Same seed, different paths = different addresses:")
    print("-" * 70)
    
    for path, description in paths:
        address = derive_with_path(TEST_MNEMONIC, path)
        print(f"\n{description}")
        print(f"  Path:    {path}")
        print(f"  Address: {address}")
    
    print()
    print("=" * 70)
    print("💡 Understanding the path: m/44'/60'/0'/0/0")
    print("  44'  = Purpose (BIP44)")
    print("  60'  = Coin type (Ethereum)")
    print("  0'   = Account (increment for new accounts)")
    print("  0    = Chain (0=external/receiving, 1=internal/change)")
    print("  0    = Address index (increment for new addresses)")
    print("  ' (apostrophe) = Hardened derivation")
    print("=" * 70)

if __name__ == "__main__":
    main()

