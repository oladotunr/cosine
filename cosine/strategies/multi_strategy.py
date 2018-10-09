"""
# 
# 09/10/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
import random
from decimal import Decimal
from cosine.core.order_worker import Pos
from cosine.strategies import locate_strategy
from .base_strategy import CosineBaseStrategy


# MODULE CLASSES
class CosineMultiStrategy(CosineBaseStrategy):

    def __init__(self, cfg, cxt, venues, pool, logger=None, **kwargs):
        super().__init__(cfg, cxt, venues, pool, logger=logger, **kwargs)
        self.strategies = map(lambda strat_name: self._create_strategy(strat_name), kwargs['strategies'])


    def setup(self):
        for strategy in self.strategies:
            strategy.setup()


    def teardown(self):
        for strategy in self.strategies:
            strategy.teardown()


    def update(self):
        self.logger.debug("MultiStrategy - ** update **")
        for strategy in self.strategies:
            strategy.update()
        self.logger.debug("MultiStrategy - ** update complete **")


    def _create_strategy(self, strat_name):
        strat = self._cfg.get("strategy", {})
        strategy_def = strat.get("settings", {}).get(strat_name, {}, split=False)
        StrategyClass = locate_strategy(module_name=strat_name)
        if not StrategyClass:
            raise ValueError("MultiStrategy - Failed to identify a valid strategy")
        self.logger.info(f"MultiStrategy - Loading CosineStrategy: [{strat_name}]")
        strategy = StrategyClass(self._cfg, self._cxt, self._venues, self._pool, logger=self.logger, **strategy_def)
        return strategy
