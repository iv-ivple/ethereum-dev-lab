"""Tests for Week 5 event scripts"""
import pytest
from unittest.mock import Mock
from web3 import Web3

@pytest.fixture
def mock_transfer_log():
    """Mock Transfer event log"""
    return {
        'address': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
        'topics': [
            '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef',  # Transfer signature
            '0x000000000000000000000000742d35cc6634c0532925a3b844bc454e4438f44e',  # from
            '0x000000000000000000000000d8da6bf26964af9d7eed9e03e53415d37aa96045'   # to
        ],
        'data': '0x00000000000000000000000000000000000000000000000000000000000f4240',  # 1000000 (1 USDC)
        'blockNumber': 18500000,
        'transactionHash': '0xabc123...',
        'logIndex': 10
    }

def parse_transfer_event(log, decimals=6):
    """Parse Transfer event from log"""
    # Handle both HexBytes and string formats
    topic1 = log['topics'][1]
    topic2 = log['topics'][2]
    
    # Convert to hex string if needed
    from_hex = topic1.hex() if hasattr(topic1, 'hex') else topic1
    to_hex = topic2.hex() if hasattr(topic2, 'hex') else topic2
    
    # Remove padding from addresses
    from_addr = '0x' + from_hex[-40:]
    to_addr = '0x' + to_hex[-40:]
    
    # Decode amount from data
    amount_raw = int(log['data'], 16)
    amount = amount_raw / (10 ** decimals)
    
    return {
        'from': Web3.to_checksum_address(from_addr),
        'to': Web3.to_checksum_address(to_addr),
        'amount': amount,
        'block': log['blockNumber'],
        'tx_hash': log['transactionHash']
    }

def test_parse_transfer_event(mock_transfer_log):
    """Test parsing Transfer event"""
    parsed = parse_transfer_event(mock_transfer_log)
    
    assert parsed['amount'] == 1.0
    assert parsed['block'] == 18500000
    assert Web3.is_address(parsed['from'])
    assert Web3.is_address(parsed['to'])

def filter_logs_by_address(logs, address):
    """Filter transfer logs for specific address"""
    address = address.lower()
    filtered = []
    
    for log in logs:
        # Handle both HexBytes and string formats
        topic1 = log['topics'][1]
        topic2 = log['topics'][2]
        
        from_hex = topic1.hex() if hasattr(topic1, 'hex') else topic1
        to_hex = topic2.hex() if hasattr(topic2, 'hex') else topic2
        
        from_addr = '0x' + from_hex[-40:]
        to_addr = '0x' + to_hex[-40:]
        
        if from_addr.lower() == address or to_addr.lower() == address:
            filtered.append(log)
    
    return filtered

def test_filter_logs_by_address(mock_transfer_log):
    """Test filtering logs by address"""
    logs = [mock_transfer_log]
    target_address = "0x742d35cc6634c0532925a3b844bc454e4438f44e"
    
    filtered = filter_logs_by_address(logs, target_address)
    
    assert len(filtered) == 1
    assert filtered[0] == mock_transfer_log
