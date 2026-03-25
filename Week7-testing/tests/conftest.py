"""Shared pytest fixtures"""
import sys
from pathlib import Path
import pytest
from web3 import Web3
from unittest.mock import Mock, MagicMock

# Add the parent directory (web3/) to Python path
root_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_dir))

@pytest.fixture
def mock_web3():
    """Mock Web3 instance for testing without real RPC calls"""
    mock_w3 = Mock(spec=Web3)
    mock_w3.eth = Mock()
    return mock_w3

@pytest.fixture
def mock_block_data():
    """Sample block data for testing"""
    return {
        'number': 18500000,
        'hash': '0xabc123...',
        'timestamp': 1699564800,
        'transactions': ['0xtx1...', '0xtx2...'],
        'gasUsed': 15000000,
        'gasLimit': 30000000
    }

@pytest.fixture
def sample_addresses():
    """Common Ethereum addresses for testing"""
    return {
        'vitalik': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
        'zero': '0x0000000000000000000000000000000000000000',
        'dead': '0x000000000000000000000000000000000000dEaD'
    }
