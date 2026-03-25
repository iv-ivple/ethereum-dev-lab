#!/usr/bin/env python3
"""
Generate HD (Hierarchical Deterministic) wallets using BIP39 mnemonic phrases.
Demonstrates derivation paths and generating multiple addresses from one seed.
"""

from mnemonic import Mnemonic
from eth_account import Account
Account.enable_unaudited_hdwallet_features()

def generate_mnemonic(strength=128):
    """
    Generate a BIP39 mnemonic phrase.
    strength: 128 bits = 12 words, 256 bits = 24 words
    """
    mnemo = Mnemonic("english")
    return mnemo.generate(strength=strength)

def derive_account(mnemonic, account_index=0):
    """
    Derive an Ethereum account from mnemonic using standard derivation path.
    Path: m/44'/60'/0'/0/{account_index}
    - 44' = BIP44
    - 60' = Ethereum
    - 0' = Account 0
    - 0 = External chain
    - account_index = Address index
    """
    derivation_path = f"m/44'/60'/0'/0/{account_index}"
    account = Account.from_mnemonic(mnemonic, account_path=derivation_path)
    
    return {
        'address': account.address,
        'private_key': account.key.hex(),
        'derivation_path': derivation_path
    }

def main():
    print("=" * 70)
    print("HD WALLET GENERATOR (BIP39/BIP44)")
    print("=" * 70)
    print()
    
    # Generate 12-word mnemonic
    mnemonic = generate_mnemonic(strength=128)
    
    print("🔑 Mnemonic Phrase (12 words):")
    print(f"   {mnemonic}")
    print()
    print("⚠️  BACKUP THIS PHRASE! It can restore ALL derived wallets.")
    print()
    
    # Derive first 3 accounts
    print("📊 Derived Accounts:")
    print("-" * 70)
    
    for i in range(3):
        account = derive_account(mnemonic, i)
        print(f"\nAccount #{i}:")
        print(f"  Path:        {account['derivation_path']}")
        print(f"  Address:     {account['address']}")
        print(f"  Private Key: {account['private_key']}")
    
    print()
    print("=" * 70)
    print("💡 Key Concepts:")
    print("  • One mnemonic → infinite addresses")
    print("  • Same mnemonic + path = same address (deterministic)")
    print("  • m/44'/60'/0'/0/X is Ethereum's standard path")
    print("  • MetaMask uses this same standard")
    print("=" * 70)

if __name__ == "__main__":
    main()
