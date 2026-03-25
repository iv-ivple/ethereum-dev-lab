"""Tests for Week 3 wallet scripts"""
import pytest
from unittest.mock import patch, Mock
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3

def generate_wallet():
    """Refactored from generate_wallet.py"""
    account = Account.create()
    return {
        'address': account.address,
        'private_key': '0x' + account.key.hex().replace('0x', ''),  # Ensure 0x prefix
        'public_key': account._key_obj.public_key.to_hex()
    }

def test_generate_wallet():
    """Test wallet generation creates valid components"""
    wallet = generate_wallet()
    
    # Verify all components exist
    assert 'address' in wallet
    assert 'private_key' in wallet
    assert 'public_key' in wallet
    
    # Verify address format
    assert Web3.is_address(wallet['address'])
    assert wallet['address'].startswith('0x')
    
    # Verify private key format (64 hex chars + 0x prefix)
    assert wallet['private_key'].startswith('0x')
    assert len(wallet['private_key']) == 66

def test_wallet_from_private_key():
    """Test recreating wallet from private key"""
    # Known private key for testing (never use in production!)
    test_private_key = "0x4c0883a69102937d6231471b5dbb6204fe512961708279f8c1c9f2e1f9c0e8a7"
    
    account = Account.from_key(test_private_key)
    
    # Verify deterministic address generation
    # Corrected expected address for this private key
    expected_address = "0xE091624C6467e0F36E2E17861F64406Fd1f67C55"
    assert account.address == expected_address

def sign_message(message, private_key):
    """Refactored from sign_message.py"""
    account = Account.from_key(private_key)
    # Use encode_defunct instead of the non-existent _hash_eip191_message
    message_encoded = encode_defunct(text=message)
    signed = account.sign_message(message_encoded)
    return signed.signature.hex()

def verify_message(message, signature, address):
    """Verify message signature"""
    message_encoded = encode_defunct(text=message)
    recovered_address = Account.recover_message(
        message_encoded,
        signature=bytes.fromhex(signature.replace('0x', ''))
    )
    return recovered_address.lower() == address.lower()

def test_sign_and_verify_message():
    """Test message signing and verification"""
    test_pk = "0x4c0883a69102937d6231471b5dbb6204fe512961708279f8c1c9f2e1f9c0e8a7"
    account = Account.from_key(test_pk)
    message = "Test message for Week 7"
    
    # Sign
    signature = sign_message(message, test_pk)
    
    # Verify
    is_valid = verify_message(message, signature, account.address)
    assert is_valid

def test_verify_invalid_signature():
    """Test that invalid signatures fail verification"""
    message = "Original message"
    fake_signature = "0x" + "00" * 65  # Invalid signature
    address = "0x962f54B95dc6e7Da32C86c765f8F3C4c0e0F5A38"
    
    with pytest.raises(Exception):  # Will raise when trying to recover
        verify_message(message, fake_signature, address)

@pytest.mark.parametrize("mnemonic_strength,expected_word_count", [
    (128, 12),
    (256, 24)
])
def test_mnemonic_generation(mnemonic_strength, expected_word_count):
    """Test mnemonic generation with different strengths"""
    Account.enable_unaudited_hdwallet_features()
    account, mnemonic = Account.create_with_mnemonic(
        num_words=expected_word_count
    )
    
    words = mnemonic.split()
    assert len(words) == expected_word_count
    assert Web3.is_address(account.address)
