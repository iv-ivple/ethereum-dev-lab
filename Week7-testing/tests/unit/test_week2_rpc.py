"""Tests for Week 2 RPC scripts"""
import pytest
from unittest.mock import patch, Mock
from web3 import Web3
from decimal import Decimal
from hexbytes import HexBytes

# Assuming you refactor your scripts to have testable functions
# If not, you'll need to do that first (see refactoring tips below)

def get_latest_block_info(w3):
    """Refactored function from get_latest_block.py"""
    block = w3.eth.get_block('latest')
    
    # Handle both HexBytes and string for hash
    block_hash = block['hash']
    if isinstance(block_hash, str):
        hash_hex = block_hash
    else:
        hash_hex = block_hash.hex()
    
    return {
        'number': block['number'],
        'hash': hash_hex,
        'timestamp': block['timestamp'],
        'transaction_count': len(block['transactions'])
    }

def test_get_latest_block_info(mock_web3, mock_block_data):
    """Test fetching latest block info"""
    # Setup mock
    mock_web3.eth.get_block.return_value = mock_block_data
    
    # Execute
    result = get_latest_block_info(mock_web3)
    
    # Verify
    assert result['number'] == 18500000
    assert result['transaction_count'] == 2
    mock_web3.eth.get_block.assert_called_once_with('latest')

def get_eth_balance(w3, address):
    """Refactored function from get_eth_balance.py"""
    if not Web3.is_address(address):
        raise ValueError(f"Invalid address: {address}")
    
    balance_wei = w3.eth.get_balance(address)
    balance_eth = Web3.from_wei(balance_wei, 'ether')
    return balance_eth

def test_get_eth_balance_valid_address(mock_web3, sample_addresses):
    """Test getting ETH balance for valid address"""
    # Setup
    mock_web3.eth.get_balance.return_value = 1000000000000000000  # 1 ETH
    
    # Execute
    balance = get_eth_balance(mock_web3, sample_addresses['vitalik'])
    
    # Verify
    assert balance == 1
    mock_web3.eth.get_balance.assert_called_once()

def test_get_eth_balance_invalid_address(mock_web3):
    """Test that invalid addresses raise ValueError"""
    with pytest.raises(ValueError, match="Invalid address"):
        get_eth_balance(mock_web3, "invalid_address")

@pytest.mark.parametrize("wei_amount,expected_eth", [
    (1000000000000000000, Decimal('1')),
    (500000000000000000, Decimal('0.5')),
    (1, Decimal('1E-18')),
    (0, Decimal('0'))
])
def test_wei_to_eth_conversion(wei_amount, expected_eth):
    """Test various Wei to ETH conversions"""
    result = Web3.from_wei(wei_amount, 'ether')
    assert result == expected_eth
