"""
# 
# 25/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
import random
from core.order_worker import Pos
from .base_strategy import CosineBaseStrategy


# MODULE CLASSES
class NoddyFloaterStrategy(CosineBaseStrategy):

    def __init__(self, cfg, cxt, venues, pool, **kwargs):
        super().__init__(cfg, cxt, venues, pool, **kwargs)


    def update(self):

        # pull instruments...
        bem_workers = self._cxt.orders.bem
        instruments = map(lambda wrkr: wrkr.instrument, bem_workers.values())

        # pull prices for instruments...
        feed = self._cxt.feeds.cryptocompare
        prices = feed.capture_latest_prices(instruments=instruments)

        # massage pricing...
        for p in self._cxt.pricer_seq:
            prices = self._cxt.pricers[p].generate_theo_prices(instrument_prices=prices)

        # update the order quotes...
        quotes = self._update_quotes(workers=bem_workers, prices=prices)

        # update the order workers...
        self._update_order_workers(workers=bem_workers, quotes=quotes)


    def _update_quotes(self, workers, prices):
        instr_quotes = {}
        instr_settings = self.instrument_settings
        for instr in prices:
            worker = workers[instr.symbol]
            stg = instr_settings.get(instr.symbol, {})
            px_info = prices[instr]
            mid_price = px_info.midprice
            spread = self.Spread
            top_spread = self.TopSpread
            max_spread = self.MaxSpread
            max_var = self.StepMaxVar
            min_step = mid_price * spread
            step = ((mid_price * top_spread) - min_step) / worker.depth
            clamp = mid_price * max_spread
            min_vol = stg.get('MinVol', 1)
            max_vol = stg.get('MaxVol', 10)
            levels = range(worker.depth)

            instr_quotes[instr] = {
                "bids": [Pos(
                    price=min(mid_price + min_step + (step * i) + (step * random.random() * max_var), mid_price + clamp),
                    openpos=( min_vol + (max_vol * i) )
                ) for i in levels],
                "asks": [Pos(
                    price=min(mid_price - min_step - (step * i) + (step * random.random() * max_var), mid_price - clamp),
                    openpos=( min_vol + (max_vol * i) )
                ) for i in levels]
            }
        return instr_quotes


    def _update_order_workers(self, workers, quotes):
        for instr in quotes:
            quote = quotes[instr]
            worker = workers[instr.symbol]
            worker.update(bids=quote['bids'], asks=quote['asks'])
