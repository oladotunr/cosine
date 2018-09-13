"""
# 
# 26/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
import ujson
import ssl
import websockets

from base64 import b64decode
from zlib import decompress, MAX_WBITS
from signalr_aio.transports import Transport as SignalRTransport
from signalr_aio import Connection as SignalRConnection

from cosine.core.proc_workers import CosineProcEventWorker
from cosine.venues.base_venue import AsyncEvents
from cosine.venues.bem.types import (
    BlockExMarketsAsyncOrder,
    BlockExMarketsAsyncExecution,
    BlockExMarketsAsyncCancelOrderResponse,
    BlockExMarketsAsyncCancelAllResponse
)


# MODULE FUNCTIONS
setattr(SignalRConnection, 'last_send_id', property(lambda self: self._Connection__send_counter))


# MODULE CLASSES
class BlockExMarketsSignalRWorker(CosineProcEventWorker):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        super().__init__(group, target, name, args, kwargs)
        self._hub = None
        self._connection = None
        self._invoke_handling = {}
        self.events.OnPlaceOrder = CosineProcEventWorker.EventSlot()
        self.events.OnExecution = CosineProcEventWorker.EventSlot()
        self.events.OnCancelOrder = CosineProcEventWorker.EventSlot()
        self.events.OnCancelAllOrders = CosineProcEventWorker.EventSlot()
        self.events.OnLatestBids = CosineProcEventWorker.EventSlot()
        self.events.OnLatestAsks = CosineProcEventWorker.EventSlot()
        self.events.OnMarketTick = CosineProcEventWorker.EventSlot()
        self.events.OnError = CosineProcEventWorker.EventSlot()


    """Worker process websockets setup"""
    def _setup_websockets_ssl_certs(self):
        cert_file = self.kwargs["CertFile"]

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_verify_locations(cert_file)

        # monkeypatch the transport to let us connect via a custom SSLContext
        async def socket(this, loop):
            async with websockets.connect(
                this._ws_params.socket_url,
                extra_headers=this._ws_params.headers,
                loop=loop,
                ssl=context
            ) as this.ws:
                this._connection.started = True
                await this.handler(this.ws)

        SignalRTransport.socket = socket


    """Worker process setup"""
    def run(self):

        # setup SSL context construction if required
        if self.kwargs["CertFile"]:
            self._setup_websockets_ssl_certs()

        # setup SignalR connection (w/ authentication)
        connection = SignalRConnection(f"{self.kwargs['APIDomain']}/signalr", session=None)
        connection.qs = {'access_token': self.kwargs['access_token']}

        hub = connection.register_hub('TradingHub')

        self._hub = hub
        self._connection = connection

        # Set event handlers
        hub.client.on('MarketTradesRefreshed', lambda x: None)
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
        if self._connection:
            self._connection.close()


    """Worker process raw message processors"""
    @staticmethod
    def process_compact_raw_msg(raw_msg):
        deflated_msg = decompress(b64decode(raw_msg), -MAX_WBITS)
        return ujson.loads(deflated_msg.decode())


    @staticmethod
    def process_raw_msg(raw_msg):
        return ujson.loads(raw_msg)


    """Worker process server invocation handling"""
    def invoke(self, method, *data, callback=None):
        inv_id = self._connection.last_send_id + 1
        self._invoke_handling[inv_id] = {"cb": callback, "a": (method, data)}
        self._hub.server.invoke(method, *data)
        return inv_id


    """Worker process raw message received"""
    async def on_raw_msg_received(self, **msg):
        if not ('I' in msg): return
        inv_id = msg['I']
        h = self._invoke_handling.get(inv_id)
        if h:
            if 'R' in msg and type(msg['R']) is not bool:
                msg = BlockExMarketsSignalRWorker.process_raw_msg(msg['R'])
            h["cb"](msg, h["a"])


    """Worker process error received"""
    async def on_error_received(self, **msg):
        self.enqueue_event(AsyncEvents.OnError, msg)


    """Worker process market tick received"""
    async def on_market_tick_received(self, msg):
        self.invoke("getBids", self.kwargs['APIID'], msg[0]['instrumentID'], callback=self.on_bids_received)


    """Worker process market tick received"""
    async def on_bids_received(self, bids_msg, req):
        (_, msg) = req
        bids_msg['instrumentID'] = msg[0]['instrumentID']
        self.enqueue_event('OnLatestBids', bids_msg)
        self.invoke("getAsks", self.kwargs['APIID'], msg[0]['instrumentID'], callback=self.on_asks_received)


    """Worker process market tick received"""
    async def on_asks_received(self, asks_msg, req):
        (_, msg) = req
        asks_msg['instrumentID'] = msg[0]['instrumentID']
        self.enqueue_event('OnLatestAsks', asks_msg)


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
