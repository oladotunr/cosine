"""
# 
# 15/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
import os

from cosine.core.config import Config, FieldSet
from cosine.core.context import CosineCoreContext
from cosine.core.proc_workers import CosineProcWorkers
from cosine.core.order_worker import CosineOrderWorker
from cosine.core.instrument import CosineInstrument
from cosine.core.utils import debounce, find_instrument
from cosine.venues import collate_venues
from cosine.pricing import collate_feeds, collate_pricers
from cosine.strategies import locate_strategy
from cosine.core.logger import create_logger


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
        self.instr_cache = FieldSet()
        self.init_logging(logger=logger)


    def init_logging(self, logger=None):
        if logger:
            self.logger = logger
            return
        self.logger = create_logger(self._args)


    def setup(self):
        self.logger.info("CosineAlgo - setup initiated")
        self._base_cfg_file = self._args.get("config", os.environ.get("COSINE_CFG", "./config.yaml"))
        self._environment = self._args.get("env", os.environ.get("COSINE_ENV", "DEV"))
        self._cfg_file = os.path.splitext(self._base_cfg_file)[0] + "." + self._environment.lower() + ".yaml"

        self._cfg = Config()
        self._cfg.load(file_path=self._base_cfg_file)
        if os.path.exists(self._cfg_file):
            self._cfg.load(file_path=self._cfg_file)
        self._cfg.Environment = self._environment
        self._cfg.CmdLnArgs = self._args
        self._cfg.log_config(logger=self.logger)

        self._worker_pool = CosineProcWorkers(self._cfg)
        self._cxt = CosineCoreContext()

        self.setup_venues()
        self.setup_order_workers()
        self.setup_pricing_feeds()
        self.setup_pricers()
        self.setup_strategy()
        self.logger.info("CosineAlgo - setup complete")


    def setup_venues(self):
        self._venues = {}
        venue_defs = self._cfg.get("venues", {})
        venue_names = venue_defs.keys()
        venues = collate_venues(venue_names)
        self.logger.info("CosineAlgo - venues:")
        for k in venue_names:
            self.logger.info(f"CosineAlgo -     Loading venue: [{k}]")
            VenueClass = venues[k]
            self._venues[k] = VenueClass(k, self._worker_pool, self._cxt, logger=self.logger, **venue_defs[k])
            self._venues[k].setup()


    def setup_order_workers(self):
        self._cxt.orders = FieldSet()
        venue_names = self._cfg.get("venues", {}).keys()
        instr_names = self._cfg.get("instruments", {})
        self.logger.info("CosineAlgo - instruments:")
        venue_instruments = 0
        for k in venue_names:
            self._cxt.orders[k] = {}
            venue = self._venues[k]
            instr_defs = venue.get_instrument_defs(instr_names)
            for instr in instr_names:
                if not (find_instrument(instr_defs, term=instr)): continue
                self.logger.info(f"CosineAlgo -     Loading instrument: [{instr}]")
                instrument = CosineInstrument.load(self.instr_cache, **instr_defs[instr])
                self._cxt.instruments[instrument.name] = instrument
                order_worker = CosineOrderWorker(self._cfg.orders.ActiveDepth, instrument, venue, logger=self.logger)
                self._cxt.orders[k][instrument.symbol] = order_worker
                venue_instruments += 1
        if venue_instruments == 0:
            raise LookupError("No instruments loaded for any of the provided venues")


    def setup_pricing_feeds(self):
        self._cxt.feeds = FieldSet()
        feed_defs = self._cfg.get("feeds", {})
        feed_names = feed_defs.keys()
        feeds = collate_feeds(feed_names)
        self.logger.info("CosineAlgo - feeds:")
        for k in feeds:
            self.logger.info(f"CosineAlgo -     Loading feed: [{k}]")
            PricingFeedClass = feeds[k]
            self._cxt.feeds[k] = PricingFeedClass(k, self._worker_pool, self._cxt, logger=self.logger, **feed_defs[k])
            self._cxt.feeds[k].setup()


    def setup_pricers(self):
        self._cxt.pricers = FieldSet()
        pricer_names = self._cfg.get("pricers", {}).get("Default", "nullpricer").split(',')
        pricer_defs = self._cfg.get("pricers", {}).get("settings", {})
        pricers = collate_pricers(pricer_names)
        self._cxt.pricer_seq = pricer_names
        self.logger.info("CosineAlgo - pricers:")
        for k in pricers:
            self.logger.info(f"CosineAlgo -     Loading pricer: [{k}]")
            PricerClass = pricers[k]
            self._cxt.pricers[k] = PricerClass(k, self._worker_pool, self._cxt, logger=self.logger, **pricer_defs[k])
            self._cxt.pricers[k].setup()


    def setup_strategy(self):
        strat = self._cfg.get("strategy", {})
        strat_name = strat.get("type")
        strategy_def = strat.get("settings", {}).get(strat_name, {}, split=False)
        StrategyClass = locate_strategy(strat_name)
        if not StrategyClass:
            raise ValueError("Failed to identify a valid strategy")
        self.logger.info(f"CosineAlgo - Loading CosineStrategy: [{strat_name}]")
        self._cxt.strategy = StrategyClass(self._cfg, self._cxt, self._venues, self._worker_pool, logger=self.logger, **strategy_def)
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
        self.logger.info("CosineAlgo - Starting algo on timer...")
        raise NotImplementedError()


    def _run_on_primary_feed(self):

        # get the primary feed...
        self.logger.info(f"CosineAlgo - Starting algo on primary feed: [{self._cfg.feed.Primary}]")
        primary_feed = self._cxt.feeds[self._cfg.feed.Primary]

        # setup the main tick handler with a debounce rate limit call rate...
        fn = debounce(wait=self._cfg.system.EventLoopThrottle)(self._tick_main)
        primary_feed.events.OnTick += fn

        # run the primary feed...
        primary_feed.run()


    def _tick_main(self):

        # update the main loop on a tick...
        self.logger.debug("CosineAlgo - ** Main loop tick **")

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

