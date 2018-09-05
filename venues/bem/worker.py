"""
# 
# 26/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
import ujson

from base64 import b64decode
from zlib import decompress, MAX_WBITS
from signalr_aio import Connection as SignalRConnection

from core.proc_workers import CosineProcWorkers
from venues.base_venue import AsyncEvents
from venues.bem.types import (
    BlockExMarketsAsyncOrder,
    BlockExMarketsAsyncExecution,
    BlockExMarketsAsyncCancelOrderResponse,
    BlockExMarketsAsyncCancelAllResponse
)


# MODULE CLASSES
class BlockExMarketsSignalRWorker(CosineProcWorkers.EventWorker):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        super().__init__(group, target, name, args, kwargs)
        self._hub = None
        self._connection = None
        self._responder = None
        self.events.OnPlaceOrder = CosineProcWorkers.EventWorker.EventSlot()
        self.events.OnExecution = CosineProcWorkers.EventWorker.EventSlot()
        self.events.OnCancelOrder = CosineProcWorkers.EventWorker.EventSlot()
        self.events.OnCancelAllOrders = CosineProcWorkers.EventWorker.EventSlot()
        self.events.OnLatestBids = CosineProcWorkers.EventWorker.EventSlot()
        self.events.OnLatestAsks = CosineProcWorkers.EventWorker.EventSlot()
        self.events.OnMarketTick = CosineProcWorkers.EventWorker.EventSlot()
        self.events.OnError = CosineProcWorkers.EventWorker.EventSlot()


    """Worker process setup"""
    def run(self):

        # setup SignalR connection (w/ authentication)
        connection = SignalRConnection(f"{self.cfg.venues.bem.APIDomain}/signalr", session=None)
        connection.qs = {'access_token': self.trade_api.access_token}

        hub = connection.register_hub('TradingHub')

        self._hub = hub
        self._connection = connection

        # Set event handlers
        hub.client.on('MarketOrdersRefreshed', self.on_market_tick_received)
        hub.client.on('tradeCreated', self.on_execution_received)
        hub.client.on('createTradeOrderResult', self.on_place_order_received)
        hub.client.on('cancelTradeOrderResult', self.on_cancel_order_received)
        hub.client.on('cancelAllTradeOrdersResult', self.on_cancel_all_orders_received)

        connection.received += self.on_raw_msg_received
        connection.error += self.on_error_received

        connection.start()
        pass


    """Worker process teardown"""
    def join(self, timeout=None):
        self._connection.close()


    """Worker process raw message processors"""
    @staticmethod
    def process_compact_raw_msg(raw_msg):
        deflated_msg = decompress(b64decode(raw_msg), -MAX_WBITS)
        return ujson.loads(deflated_msg.decode())


    @staticmethod
    def process_raw_msg(raw_msg):
        return ujson.loads(raw_msg)


    """Worker process raw message received"""
    async def on_raw_msg_received(self, msg):
        if 'R' in msg and type(msg['R']) is not bool:
            if self._responder:
                msg = BlockExMarketsSignalRWorker.process_raw_msg(msg['R'])
                self._responder(msg)
                self._responder = None


    """Worker process error received"""
    async def on_error_received(self, msg):
        self.enqueue_event(AsyncEvents.OnError, msg)


    """Worker process market tick received"""
    async def on_market_tick_received(self, msg):
        self._responder = self.on_bids_received
        self._hub.server.invoke("getBids", self.cfg.venues.bem.APIID, msg['instrumentID'])


    """Worker process market tick received"""
    async def on_bids_received(self, msg):
        self.enqueue_event('OnLatestBids', msg)
        self._responder = self.on_asks_received
        self._hub.server.invoke("getAsks", self.cfg.venues.bem.APIID, msg['instrumentID'])


    """Worker process market tick received"""
    async def on_asks_received(self, msg):
        self.enqueue_event('OnLatestAsks', msg)


    """Worker process place order response received"""
    async def on_place_order_received(self, msg):
        self.enqueue_event(AsyncEvents.OnPlaceOrder, BlockExMarketsAsyncOrder(signalr_msg=msg))


    """Worker process place order response received"""
    async def on_execution_received(self, msg):
        self.enqueue_event(AsyncEvents.OnExecution, BlockExMarketsAsyncExecution(signalr_msg=msg))


    """Worker process cancel order response received"""
    async def on_cancel_order_received(self, msg):
        self.enqueue_event(AsyncEvents.OnCancelOrder, BlockExMarketsAsyncCancelOrderResponse(signalr_msg=msg))


    """Worker process cancel all response received"""
    async def on_cancel_all_orders_received(self, msg):
        self.enqueue_event(AsyncEvents.OnCancelAllOrders, BlockExMarketsAsyncCancelAllResponse(signalr_msg=msg))
