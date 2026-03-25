"""Tests for Week 4 ERC-20 scripts"""
import pytest
from unittest.mock import Mock, MagicMock
from web3 import Web3

@pytest.fixture
def mock_erc20_contract():
    """Mock ERC-20 contract"""
    contract = Mock()
    contract.address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"  # USDC
    
    # Mock functions
    contract.functions.name.return_value.call.return_value = "USD Coin"
    contract.functions.symbol.return_value.call.return_value = "USDC"
    contract.functions.decimals.return_value.call.return_value = 6
    contract.functions.totalSupply.return_value.call.return_value = 25000000000000000
    contract.functions.balanceOf.return_value.call.return_value = 1000000000  # 1000 USDC
    
    return contract

def get_token_metadata(contract):
    """Get ERC-20 token metadata"""
    return {
        'name': contract.functions.name().call(),
        'symbol': contract.functions.symbol().call(),
        'decimals': contract.functions.decimals().call(),
        'total_supply': contract.functions.totalSupply().call()
    }

def test_get_token_metadata(mock_erc20_contract):
    """Test fetching token metadata"""
    metadata = get_token_metadata(mock_erc20_contract)
    
    assert metadata['name'] == "USD Coin"
    assert metadata['symbol'] == "USDC"
    assert metadata['decimals'] == 6
    assert metadata['total_supply'] == 25000000000000000

def get_token_balance(contract, address, decimals):
    """Get formatted token balance"""
    raw_balance = contract.functions.balanceOf(address).call()
    formatted_balance = raw_balance / (10 ** decimals)
    return formatted_balance

def test_get_token_balance(mock_erc20_contract, sample_addresses):
    """Test getting token balance"""
    balance = get_token_balance(
        mock_erc20_contract,
        sample_addresses['vitalik'],
        6
    )
    
    assert balance == 1000.0  # 1000000000 / 10^6

@pytest.mark.parametrize("raw_balance,decimals,expected", [
    (1000000, 6, 1.0),
    (1500000, 6, 1.5),
    (1000000000000000000, 18, 1.0),
    (0, 18, 0.0)
])
def test_balance_formatting(raw_balance, decimals, expected):
    """Test balance formatting with various decimals"""
    result = raw_balance / (10 ** decimals)
    assert result == expected
