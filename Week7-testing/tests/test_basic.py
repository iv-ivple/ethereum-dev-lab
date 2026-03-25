"""Basic tests to verify pytest is working"""
import pytest
from web3 import Web3

def test_web3_import():
    """Test that web3 imports correctly"""
    assert Web3 is not None

def test_wei_conversion():
    """Test Wei to Ether conversion"""
    wei_amount = 1000000000000000000  # 1 ETH in Wei
    eth_amount = Web3.from_wei(wei_amount, 'ether')
    assert eth_amount == 1

def test_address_validation():
    """Test address validation"""
    valid_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    assert Web3.is_address(valid_address)
    
    invalid_address = "not_an_address"
    assert not Web3.is_address(invalid_address)

def test_checksum_address():
    """Test address checksumming"""
    lowercase_addr = "0x742d35cc6634c0532925a3b844bc454e4438f44e"
    checksum_addr = Web3.to_checksum_address(lowercase_addr)
    assert checksum_addr == "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
