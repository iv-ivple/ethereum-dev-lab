from typing import Optional
from keeper.scanner.opportunity_scanner import BaseScanner, Opportunity
from arb.scanner import run_scan           # your existing scanner
from arb.optimizer import find_optimal_input
from gas.advanced_gas_calculator import calculate_arb_gas_cost
from keeper.config import config

class ArbStrategy(BaseScanner):
    async def scan(self, block_number: int) -> Optional[Opportunity]:
        results = run_scan()  # returns list of ArbitrageOpportunity from Week 28–30
        if not results:
            return None
        best = max(results, key=lambda r: r.net_profit_eth)
        if best.net_profit_eth < config.min_profit_eth:
            return None
        return Opportunity(
            strategy="arb_triangle",
            description=best.path_description,
            gross_profit_eth=best.gross_profit_eth,
            gas_cost_eth=best.gas_cost_eth,
            net_profit_eth=best.net_profit_eth,
            input_amount_eth=best.input_amount_eth,
            metadata={"path": best.path, "pairs": best.pair_addresses},
        )
