#!/usr/bin/env python3
"""
Sign and verify messages with Ethereum private keys.
Demonstrates EIP-191 message signing standard.
"""

from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3

def sign_message(private_key, message):
    """Sign a message with a private key."""
    account = Account.from_key(private_key)
    
    # Encode message according to EIP-191
    message_encoded = encode_defunct(text=message)
    
    # Sign the message
    signed_message = account.sign_message(message_encoded)
    
    return {
        'message': message,
        'signature': signed_message.signature.hex(),
        'messageHash': signed_message.message_hash.hex(),
        'r': hex(signed_message.r),
        's': hex(signed_message.s),
        'v': signed_message.v
    }

def verify_signature(message, signature, expected_address):
    """Verify a signature and recover the signer's address."""
    message_encoded = encode_defunct(text=message)
    
    # Recover address from signature
    recovered_address = Account.recover_message(message_encoded, signature=signature)
    
    is_valid = recovered_address.lower() == expected_address.lower()
    
    return {
        'is_valid': is_valid,
        'recovered_address': recovered_address,
        'expected_address': expected_address
    }

def main():
    print("=" * 70)
    print("MESSAGE SIGNING & VERIFICATION")
    print("=" * 70)
    print()
    
    # Generate a test wallet
    account = Account.create()
    private_key = account.key.hex()
    address = account.address
    
    print(f"Test Wallet Address: {address}")
    print()
    
    # Message to sign
    message = "I agree to the terms and conditions on 2024-01-15"
    
    print(f"📝 Message to sign:")
    print(f"   '{message}'")
    print()
    
    # Sign the message
    signed = sign_message(private_key, message)
    
    print("✍️  Signature Components:")
    print(f"   Full Signature: {signed['signature']}")
    print(f"   Message Hash:   {signed['messageHash']}")
    print(f"   r: {signed['r']}")
    print(f"   s: {signed['s']}")
    print(f"   v: {signed['v']}")
    print()
    
    # Verify the signature
    verification = verify_signature(message, signed['signature'], address)
    
    print("✅ Signature Verification:")
    print(f"   Valid: {verification['is_valid']}")
    print(f"   Recovered Address: {verification['recovered_address']}")
    print(f"   Expected Address:  {verification['expected_address']}")
    print()
    
    # Test with wrong message
    print("🧪 Testing with tampered message:")
    tampered_message = "I agree to DIFFERENT terms"
    verification_bad = verify_signature(tampered_message, signed['signature'], address)
    print(f"   Valid: {verification_bad['is_valid']}")
    print(f"   Recovered: {verification_bad['recovered_address']}")
    print()
    
    print("=" * 70)
    print("💡 Use Cases for Message Signing:")
    print("  • Prove wallet ownership without sending transaction")
    print("  • Sign-in with Ethereum (authentication)")
    print("  • Off-chain agreements and attestations")
    print("  • Meta-transactions and gasless approvals")
    print("=" * 70)

if __name__ == "__main__":
    main()
