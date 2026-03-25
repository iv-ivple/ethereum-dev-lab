#!/usr/bin/env python3
"""
Generate a new Ethereum wallet with private key, public key, and address.
⚠️  FOR EDUCATIONAL PURPOSES ONLY - NEVER use these wallets for real funds!
"""

from eth_account import Account
import secrets

def generate_wallet():
    """Generate a new Ethereum wallet."""
    
    # Generate a secure random private key (32 bytes = 256 bits)
    private_key = "0x" + secrets.token_hex(32)
    
    # Create account from private key
    account = Account.from_key(private_key)
    
    return {
        'private_key': private_key,
        'address': account.address,
        'public_key': account._key_obj.public_key.to_hex()
    }

def main():
    print("=" * 60)
    print("ETHEREUM WALLET GENERATOR")
    print("⚠️  FOR EDUCATIONAL PURPOSES ONLY!")
    print("=" * 60)
    print()
    
    wallet = generate_wallet()
    
    print("✅ New wallet generated successfully!")
    print()
    print(f"Address:     {wallet['address']}")
    print(f"Private Key: {wallet['private_key']}")
    print(f"Public Key:  {wallet['public_key']}")
    print()
    print("⚠️  SECURITY WARNINGS:")
    print("1. NEVER share your private key with anyone")
    print("2. NEVER commit private keys to git")
    print("3. This is for testing only - use on testnets only!")
    print("=" * 60)

if __name__ == "__main__":
    main()

