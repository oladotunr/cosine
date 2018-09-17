"""
# 
# 15/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
from decimal import Decimal
from cosine.core.logger import null_logger
from cosine.core.config import FieldSet
from cosine.core.proc_workers import CosineProcEventWorker
from cosine.core.utils import CosineEventSlot


# MODULE CLASSES
class CosineFeedProcWorker(CosineProcEventWorker):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        super().__init__(group, target, name, args, kwargs)
        self._hub = None
        self._connection = None
        self._responder = None
        self.events.OnRawTick = CosineEventSlot()

    def run(self):
        feed = self.kwargs['feed']
        feed.run()


class CosineBaseFeed(object):

    def __init__(self, name, pool, cxt, logger=None, **kwargs):
        [setattr(self, k, kwargs[k]) for k in kwargs]
        self.logger = logger if logger else null_logger
        self._feed_name = name
        self._pool = pool
        self._cfg = self._pool.cfg
        self._cxt = cxt
        self._cache = {}
        self._worker = None
        self._events = FieldSet()
        self._events.OnTick = CosineEventSlot()


    def setup(self):
        self._init_pricing_cache()

        if self._cfg.system.EventLoop == "feed" and self._cfg.feed.Primary != self._feed_name:
            return self._run_via_worker()


    def teardown(self):
        pass


    def update(self):
        if self._worker:
            self._worker.process_events()


    """Worker process run or inline run"""
    def run(self):
        raise NotImplementedError()


    def capture_latest_prices(self, instruments):
        return {
            instr: self._cache[instr.name] for instr in instruments if instr.name in self._cache
        }


    def _init_pricing_cache(self):
        instruments = self.instruments
        for instr_name in instruments:
            instr_feed_data = instruments.get(instr_name)
            instrument = self._cxt.find_instrument(term=instr_name)
            if not instrument: continue
            if instr_feed_data:
                instrument.symbology.attrs[self._feed_name] = instr_feed_data
            self._cache[instrument.name] = FieldSet(
                instrument=instrument,
                lastmarket=None,
                lasttraded=Decimal(0.0),
                midprice=Decimal(0.0),
                bid=Decimal(0.0),
                offer=Decimal(0.0),
                average=Decimal(0.0),
                openhour=Decimal(0.0),
                highhour=Decimal(0.0),
                lowhour=Decimal(0.0),
                openday=Decimal(0.0),
                highday=Decimal(0.0),
                lowday=Decimal(0.0),
                lasttradedvol=Decimal(0.0),
                lasttradedvolccy=Decimal(0.0),
                dayvol=Decimal(0.0),
                dayvolccy=Decimal(0.0)
            )
        self._snapshot_cache()


    def _snapshot_cache(self):
        raise NotImplementedError()


    def _run_via_worker(self):
        self._worker = CosineFeedProcWorker()
        self._setup_events(self._worker)
        self._worker.run_via(self._pool, feed=self)


    def _setup_events(self, worker):
        pass


    @property
    def events(self):
        return self._events

