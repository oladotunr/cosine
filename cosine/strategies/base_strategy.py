"""
# 
# 15/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
from cosine.core.utils import find_by_instrument, find_instrument
from cosine.core.logger import null_logger


# MODULE CLASSES
class CosineBaseStrategy(object):

    def __init__(self, cfg, cxt, venues, pool, logger=None, **kwargs):
        [setattr(self, k, kwargs[k]) for k in kwargs]
        self.logger = logger if logger else null_logger
        self._cfg = cfg
        self._cxt = cxt
        self._venues = venues
        self._pool = pool


    def setup(self):
        pass


    def teardown(self):
        pass


    def update(self):
        raise NotImplementedError()


    def find_instrument(self, instruments, term):
        return find_instrument(instruments, term=term)

    def find_by_instrument(self, instr_data, instr):
        return find_by_instrument(instr_data, instr=instr)


    def _get_venue_orderworkers(self, venue_module):
        return self._cxt.orders[venue_module]

    def _get_instruments_for_orderworkers(self, oworkers):
        return map(lambda wrkr: wrkr.instrument, oworkers.values())

    def _get_instruments_for_venue(self, venue_module):
        bem_workers = self._get_venue_orderworkers(venue_module)
        return map(lambda wrkr: wrkr.instrument, bem_workers.values())

    def _capture_feed_prices(self, feed_module, instruments):
        feed = self._cxt.feeds[feed_module]
        return feed.capture_latest_prices(instruments=instruments)

    def _run_pipelined_pricers(self, prices, cls=None):
        cls = cls if cls is not None else self.__name__
        for p in self._cxt.pricer_seq:
            self.logger.debug(f"{cls} - calc pricing: [{p}]")
            prices = self._cxt.pricers[p].generate_theo_prices(instrument_prices=prices)
        return prices

