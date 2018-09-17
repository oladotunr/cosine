"""
# 
# 15/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
import inspect
from enum import Enum
from cosine.core.logger import null_logger


# MODULE CLASSES
class OfferType(Enum):
    Bid = 1
    Ask = 2


class OrderType(Enum):
    Limit = 1
    Market = 2
    Stop = 3


class OrderStatus(Enum):
    Pending = 10
    Failed = 15
    Placed = 20
    Rejected = 30
    Cancelled = 40
    PartiallyExecuted = 50
    Executed = 60


class AsyncEvents:
    OnPlaceOrder = "OnPlaceOrder"
    OnCancelOrder = "OnCancelOrder"
    OnCancelAllOrders = "OnCancelAllOrders"
    OnExecution = "OnExecution"
    OnMarketTick = "OnMarketTick"
    OnError = "OnError"

    @classmethod
    def has(cls, k):
        return k in inspect.getmembers(cls, lambda x: type(x) == str)


class CosineNewOrder(object):

    @property
    def placed(self):
        raise NotImplementedError()

    @property
    def id(self):
        raise NotImplementedError()


class CosineOrder(object):

    @property
    def id(self):
        raise NotImplementedError()

    @property
    def price(self):
        raise NotImplementedError()

    @property
    def initial_qty(self):
        raise NotImplementedError()

    @property
    def remaining_qty(self):
        raise NotImplementedError()

    @property
    def created_at(self):
        raise NotImplementedError()

    @property
    def side(self):
        raise NotImplementedError()

    @property
    def instrument_venue_id(self):
        raise NotImplementedError()

    @property
    def status(self):
        raise NotImplementedError()




class CosineExecution(object):

    @property
    def id(self):
        raise NotImplementedError()

    @property
    def ask_order_id(self):
        raise NotImplementedError()

    @property
    def bid_order_id(self):
        raise NotImplementedError()

    @property
    def instrument_venue_id(self):
        raise NotImplementedError()

    @property
    def price(self):
        raise NotImplementedError()

    @property
    def qty(self):
        raise NotImplementedError()

    @property
    def exec_time(self):
        raise NotImplementedError()


class CosineCancelOrderResponse(object):

    @property
    def cancelled(self):
        raise NotImplementedError()

    @property
    def order_id(self):
        return None


class CosineCancelAllResponse(object):

    @property
    def cancelled(self):
        raise NotImplementedError()

    @property
    def cancelled_order_ids(self):
        return []

    @property
    def failed_order_ids(self):
        return []


class CosineBalanceInfo(object):

    @property
    def balances(self):
        raise NotImplementedError()


class CosineBaseVenue(object):

    def __init__(self, name, worker_pool, cxt, logger=None, **kwargs):
        [setattr(self, k, kwargs[k]) for k in kwargs]
        self.name = name
        self.logger = logger if logger else null_logger
        self._cxt = cxt
        self._pool = worker_pool

    def setup(self):
        raise NotImplementedError()

    def teardown(self):
        raise NotImplementedError()

    def update(self):
        pass

    def on(self, event_name, handler):
        raise NotImplementedError()

    def get_instrument_defs(self):
        raise NotImplementedError()

    def get_open_orders(self, instrument, order_type=None, offer_type=None, max_count=100):
        raise NotImplementedError()

    def get_inventory(self):
        raise NotImplementedError()

    def new_order(self, offer_type, order_type, instrument, price, quantity, attrs=None):
        raise NotImplementedError()

    def cancel_order(self, order):
        raise NotImplementedError()

    def cancel_all_orders(self, instrument):
        raise NotImplementedError()

    @property
    def is_async(self):
        return False

