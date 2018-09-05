"""
# 
# 15/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
import os
import argparse

from core.config import Config, Namespace
from core.context import CosineCoreContext
from core.proc_workers import CosineProcWorkers
from core.order_worker import CosineOrderWorker
from core.instrument import CosineInstrument
from core.utils import debounce
from venues import collate_venues
from pricing import collate_feeds, collate_pricers
from strategies import locate_strategy
from core.logger import create_logger


# MODULE CLASSES
class CosineAlgo(object):

    def __init__(self, cmdline_args, logger=None):
        self._cfg = None
        self._cxt = None
        self._worker_pool = None
        self._venues = None
        self._base_cfg_file = None
        self._environment = None
        self._cfg_file = None
        self.logger = None
        self._args = cmdline_args
        self.instr_cache = Namespace()
        self.init_logging(logger=logger)


    def init_logging(self, logger=None):
        if logger:
            self.logger = logger
            return
        self.logger = create_logger(self._args)


    def setup(self):
        self._base_cfg_file = os.environ.get("COSINE_CFG", self._args.get("config", "./config.yaml"))
        self._environment = os.environ.get("COSINE_ENV", self._args.get("env", "DEV"))
        self._cfg_file = os.path.splitext(self._base_cfg_file)[0] + self._environment.lower() + ".yaml"

        self._cfg = Config()
        self._cfg.load(file_path=self._base_cfg_file)
        self._cfg.load(file_path=self._cfg_file)
        self._cfg.Environment = self._environment
        self._cfg.CmdLnArgs = self._args

        self._worker_pool = CosineProcWorkers(self._cfg)
        self._cxt = CosineCoreContext()

        self.setup_venues()
        self.setup_order_workers()
        self.setup_pricing_feeds()
        self.setup_pricers()
        self.setup_strategy()


    def setup_venues(self):
        self._venues = {}
        venue_defs = self._cfg.get("venues", {})
        venue_names = venue_defs.keys()
        venues = collate_venues(venue_names)
        for k in venue_names:
            VenueClass = venues[k]
            self._venues[k] = VenueClass(self._worker_pool, self._cxt, **venue_defs)
            self._venues[k].setup()


    def setup_order_workers(self):
        self._cxt.orders = Namespace()
        venue_names = self._cfg.get("venues", {}).keys()
        instr_names = self._cfg.get("instruments", {})
        for k in venue_names:
            self._cxt.orders[k] = {}
            venue = self._venues[k]
            instr_defs = venue.get_instrument_defs(instr_names)
            for instr in instr_names:
                if not (instr in instr_defs): continue
                self.logger.info("Loading instrument: "+instr)
                instrument = CosineInstrument.load(self.instr_cache, instr_defs[instr])
                self._cxt.instruments[instrument.name] = instrument
                order_worker = CosineOrderWorker(self._cfg.orders.ActiveDepth, instrument, venue)
                self._cxt.orders[k][instr.symbol] = order_worker


    def setup_pricing_feeds(self):
        self._cxt.feeds = Namespace()
        feed_defs = self._cfg.get("feeds", {})
        feed_names = feed_defs.keys()
        feeds = collate_feeds(feed_names)
        for k in feeds:
            PricingFeedClass = feeds[k]
            self._cxt.feeds[k] = PricingFeedClass(k, self._worker_pool, self._cxt, **feeds[k])
            self._cxt.feeds[k].setup()


    def setup_pricers(self):
        self._cxt.pricers = Namespace()
        pricer_names = self._cfg.get("pricers", "nullpricer").split(',')
        pricer_defs = self._cfg.get("pricers", {}).get("settings", {})
        pricers = collate_pricers(pricer_names)
        self._cxt.pricer_seq = pricer_names
        for k in pricers:
            PricerClass = pricers[k]
            self._cxt.pricers[k] = PricerClass(k, self._worker_pool, self._cxt, **pricer_defs[k])
            self._cxt.pricers[k].setup()


    def setup_strategy(self):
        strat = self._cfg.get("strategy", {})
        strat_name = strat.get("type")
        strategy_def = strat.get("settings", {}).get(strat_name, {})
        StrategyClass = locate_strategy(strat_name)
        if not StrategyClass:
            raise ValueError("Failed to identify a valid strategy")
        self._cxt.strategy = StrategyClass(self._cfg, self._cxt, self._venues, self._worker_pool, **strategy_def)
        self._cxt.strategy.setup()


    def teardown(self):
        self._cxt.strategy.teardown()
        for k in self._cxt.pricers:
            self._cxt.pricers[k].teardown()

        for k in self._cxt.feeds:
            self._cxt.feeds[k].teardown()

        for k in self._cxt.orders:
            for sym in self._cxt.orders[k]:
                self._cxt.orders[k][sym].pull_all()

        for k in self._venues:
            self._venues[k].teardown()

        self.worker_pool.join(timeout=self._cfg.system.get("JoinTimeout"))


    def run(self):

        # setup the algo...
        self.setup()

        # initiate the update loop...
        if self._cfg.system.EventLoop == "feed":

            # here we tick the strategy every time the primary pricing feed ticks...
            self._run_on_primary_feed()
        else:
            # here we tick the strategy every time the timer ticks...
            self._run_on_timer()

        # clean up the algo and exit...
        return self.teardown()


    def _run_on_timer(self):
        raise NotImplementedError()


    def _run_on_primary_feed(self):

        # get the primary feed...
        primary_feed = self._cxt.feeds[self._cfg.feed.Primary]

        # setup the main tick handler with a debounce rate limit call rate...
        fn = debounce(wait=self._cfg.system.EventLoopThrottle)(self._tick_main)
        primary_feed.events.OnTick += fn

        # run the primary feed...
        primary_feed.run()


    def _tick_main(self):

        # update the main loop on a tick...

        # update aux pricing...
        for k in self._cxt.feeds:
            self._cxt.feeds[k].update()

        # update the venues...
        for k in self._venues:
            self._venues[k].update()

        # update the strategy...
        self._cxt.strategy.update()


    @property
    def worker_pool(self):
        return self._worker_pool

