from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class Opportunity:
    strategy: str
    description: str
    gross_profit_eth: float
    gas_cost_eth: float
    net_profit_eth: float
    input_amount_eth: float
    metadata: dict   # strategy-specific data needed for execution

class BaseScanner(ABC):
    @abstractmethod
    async def scan(self, block_number: int) -> Optional[Opportunity]:
        """
        Called on every new block. Return an Opportunity if one exists,
        None otherwise. Must be fast — you have ~12 seconds before the next block.
        """
        ...
