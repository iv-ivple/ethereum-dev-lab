import sys
from unittest.mock import MagicMock

# Stub out the entire arb dependency tree before any test imports keeper_bot.
# This prevents the real arb/scanner.py (and its transitive deps like
# multi_hop_quote) from being imported at all.
sys.modules.setdefault("arb", MagicMock())
sys.modules.setdefault("arb.scanner", MagicMock())
sys.modules.setdefault("arb.optimizer", MagicMock())
sys.modules.setdefault("multi_hop_quote", MagicMock())
sys.modules.setdefault("gas", MagicMock())
sys.modules.setdefault("gas.gas_oracle", MagicMock())
sys.modules.setdefault("gas.advanced_gas_calculator", MagicMock())
