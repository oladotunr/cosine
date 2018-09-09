"""
# 
# 21/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
from cosine.core.config import Namespace
from cosine.core.logger import logger
from cosine.venues.base_venue import CosineBaseVenue, AsyncEvents
from cosine.venues.bem.worker import BlockExMarketsSignalRWorker
from cosine.venues.bem.types import BlockExMarketsOrder, BlockExMarketsBalanceInfo
from blockex.tradeapi import interface
from blockex.tradeapi.tradeapi import BlockExTradeApi
from blockex.tradeapi.helper import message_raiser, get_error_message


# MODULE FUNCTIONS
API_GET_ACTIVE_CCYS = "api/lookups/currencies"
API_GET_QUOTE_CCYS = "api/lookups/quotecurrencies"


def get_active_currencies(self):
    response = self.make_authorized_request(self.get_path, API_GET_ACTIVE_CCYS)
    if response.status_code == interface.SUCCESS:
        ccys = response.json()
        return ccys

    message_raiser('Failed to get the active currencies. {error_message}',
                   error_message=get_error_message(response))

def get_quote_currencies(self):
    response = self.make_authorized_request(self.get_path, API_GET_QUOTE_CCYS)
    if response.status_code == interface.SUCCESS:
        ccys = response.json()
        return ccys

    message_raiser('Failed to get the quote currencies. {error_message}',
                   error_message=get_error_message(response))


# MODULE CLASSES
class BlockExMarketsVenue(CosineBaseVenue):

    def __init__(self, worker_pool, cxt, **kwargs):
        super().__init__(worker_pool, cxt, **kwargs)
        self._currencies = None
        self._instruments = None
        self.trade_api = None
        self._worker = BlockExMarketsSignalRWorker()
        self.cfg = self._pool.cfg


    def setup(self):
        # initialise the HTTP API
        self.trade_api = BlockExTradeApi(
            self.cfg.venues.bem.Username,
            self.cfg.venues.bem.Password,
            self.cfg.venues.bem.APIDomain,
            self.cfg.venues.bem.APIID
        )

        # initialise the streaming API
        if self.cfg.venues.bem.ConnectSignalR:
            self._setup_signalr_stream()

        # bootstrap the API with some more functions:
        self.trade_api.get_active_currencies = get_active_currencies.__get__(self.trade_api, BlockExTradeApi)
        self.trade_api.get_quote_currencies = get_quote_currencies.__get__(self.trade_api, BlockExTradeApi)

        # retrieve all the currencies supported...
        build_ccy = lambda ccy: Namespace(
            venue_id=ccy["id"],
            name=ccy["currencyName"],
            symbol=ccy["symbol"],
            category="crypto" if ccy["type"] is not "fiat" else "fiat",
            type=ccy["type"],
            precision=ccy["precision"],
            symbology={
                "symbol": ccy["symbol"],
                "iso": ccy["isoCode"],
                "label": ccy["description"],
            }
        )
        self._currencies = {
            ccy["id"]: build_ccy(ccy)
            for ccy in (self.trade_api.get_active_currencies() + self.trade_api.get_quote_currencies())
        }

        # retrieve all the instruments supported...
        self._get_instruments()


    def teardown(self):
        # the pool will handle worker clean up for us so nothing to do here...
        return self


    def update(self):
        self._worker.process_events()
        return self


    def on(self, event_name, handler):
        this = self
        if event_name == AsyncEvents.OnMarketTick:

            # define a tick conflation function...
            def conflate_market_tick(h):
                tick = {}
                def finalise(msg):
                    if 'bids' in msg and 'asks' in msg:
                        h(msg)
                        msg.clear()

                def on_bids(msg):
                    tick['bids'] = msg['orders']
                    finalise(tick)

                def on_asks(msg):
                    tick['asks'] = msg['orders']
                    finalise(tick)

                this.events.OnLatestBids += on_bids
                this.events.OnLatestAsks += on_asks

            self.events[event_name] += conflate_market_tick(handler)
        elif AsyncEvents.has(event_name):
            self.events[event_name] += handler
        return self


    def get_instrument_defs(self, filtered_instr_names=None):
        return {
            instr.name: instr for instr in self._instruments if instr.name in filtered_instr_names
        } if filtered_instr_names else self._instruments


    def _get_instruments(self):
        trader_instruments = self.trade_api.get_trader_instruments()
        self._instruments = [Namespace(
            cls="CosinePairInstrument",

            asset=self._currencies[bem_instr["baseCurrencyID"]],
            quote_ccy=self._currencies[bem_instr["quoteCurrencyID"]],

            name=bem_instr["name"],
            symbol=bem_instr["name"],
            venue_id=bem_instr["id"],

            category="crypto",
            type="pair",
            precision=self._currencies[bem_instr["quoteCurrencyID"]].precision,
            symbology={
                "symbol": bem_instr["name"],
                "label": self._currencies[bem_instr["baseCurrencyID"]].symbology["label"],
                "venue_asset_id": bem_instr["baseCurrencyID"],
                "venue_ccy_id": bem_instr["quoteCurrencyID"],
            }
        ) for bem_instr in trader_instruments]


    def get_inventory(self):
        balance_info = BlockExMarketsBalanceInfo(api_msg=self.trade_api.get_trader_info())
        balance_info.set_instrument_defs(self._instruments)
        return balance_info


    def get_open_orders(self, instrument, order_type=None, offer_type=None, max_count=100):
        orders = self.trade_api.get_orders(
            instrument_id=instrument.venue_id,
            order_type=order_type,
            offer_type=offer_type,
            status=[10,20,50],
            max_count=max_count
        )
        return map(lambda msg: BlockExMarketsOrder(api_msg=msg), orders)


    def new_order(self, offer_type, order_type, instrument, price, quantity, attrs=None):
        msg = self.trade_api.create_order(offer_type, order_type, instrument.venue_id, price, quantity)
        return BlockExMarketsOrder(api_msg=msg)


    def cancel_order(self, order):
        self.trade_api.cancel_order(order.id)


    def cancel_all_orders(self, instrument):
        self.trade_api.cancel_all_orders(instrument.venue_id)


    @staticmethod
    def on_error(msg):
        logger.error(msg)


    def _setup_signalr_stream(self):
        # setup any message handlers...
        self._worker.events.OnError += BlockExMarketsVenue.on_error

        # kick off the worker thread...
        self._worker.run_via(self._pool)


    @property
    def is_async(self):
        return True


    @property
    def events(self):
        return self._worker.events