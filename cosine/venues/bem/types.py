"""
# 
# 26/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
from datetime import datetime
from decimal import Decimal
from cosine.core.config import FieldSet
from cosine.venues.base_venue import (
    OfferType, OrderType, OrderStatus,
    CosineNewOrder,
    CosineOrder,
    CosineExecution,
    CosineCancelOrderResponse,
    CosineCancelAllResponse,
    CosineBalanceInfo
)


# MODULE CLASSES
class BlockExMarketsAsyncOrder(CosineNewOrder):

    def __init__(self, signalr_msg):
        self._msg = dict(**signalr_msg)

    @property
    def placed(self):
        return self._msg['isSuccessful']

    @property
    def id(self):
        return self._msg['orderID']

    @property
    def reject_reason(self):
        return self._msg['rejectReason']


class BlockExMarketsAsyncExecution(CosineExecution):

    def __init__(self, signalr_msg):
        self._msg = dict(**signalr_msg)
        self._msg['price'] = Decimal(self._msg['price'])
        self._msg['quantity'] = Decimal(self._msg['quantity'])

    @property
    def id(self):
        return self._msg['id']

    @property
    def ask_order_id(self):
        return self._msg['askTradeOrderID']

    @property
    def bid_order_id(self):
        return self._msg['bidTradeOrderID']

    @property
    def instrument_venue_id(self):
        return self._msg['instrumentID']

    @property
    def price(self):
        return self._msg['price']

    @property
    def qty(self):
        return self._msg['quantity']

    @property
    def exec_time(self):
        return self._msg['executedOn']


class BlockExMarketsAsyncCancelOrderResponse(CosineCancelOrderResponse):

    def __init__(self, signalr_msg):
        self._msg = dict(**signalr_msg)

    @property
    def cancelled(self):
        return self._msg['isSuccessful']

    @property
    def order_id(self):
        return self._msg['orderID']


class BlockExMarketsAsyncCancelAllResponse(CosineCancelAllResponse):

    def __init__(self, signalr_msg):
        self._msg = dict(**signalr_msg)

    @property
    def cancelled(self):
        return self._msg['isSuccessful']

    @property
    def cancelled_order_ids(self):
        return self._msg['cancelledOrderIDs']

    @property
    def failed_order_ids(self):
        return self._msg['failedOrderIDs']


class Balance(FieldSet):
    pass


class BlockExMarketsBalanceInfo(CosineBalanceInfo):

    def __init__(self, api_msg):
        self._msg = dict(**api_msg)
        self._instruments = None
        self._balances = {
            ccy["currencyName"]: Balance(
                real_balance=ccy["realBalance"],
                available_balance=ccy["availableBalance"]
            )
            for ccy in self._msg.get('currenciesTotals', [])
        }

    def set_instrument_defs(self, instrument_defs):
        self._instruments = instrument_defs
        for instr in self._instruments:
            if not (instr.asset.symbol in self._balances) and instr.asset.name in self._balances:
                self._balances[instr.asset.symbol] = self._balances[instr.asset.name]
            elif not (instr.asset.symbol in self._balances) and instr.asset.symbology['name'] in self._balances:
                self._balances[instr.asset.symbol] = self._balances[instr.asset.symbology['name']]

            if not (instr.quote_ccy.symbol in self._balances) and instr.quote_ccy.name in self._balances:
                self._balances[instr.quote_ccy.symbol] = self._balances[instr.quote_ccy.name]
            elif not (instr.quote_ccy.symbol in self._balances) and instr.quote_ccy.symbology['name'] in self._balances:
                self._balances[instr.quote_ccy.symbol] = self._balances[instr.quote_ccy.symbology['name']]

    @property
    def balances(self):
        return self._balances


class BlockExMarketsOrder(CosineOrder):

    def __init__(self, api_msg):
        self._msg = dict(**api_msg)
        self._msg['price'] = Decimal(self._msg['price'])
        self._msg['initialQuantity'] = Decimal(self._msg['initialQuantity'])
        self._msg['quantity'] = Decimal(self._msg['quantity'])
        self._msg['offerType'] = OfferType(self._msg['offerType'])
        self._msg['status'] = OrderStatus(self._msg['status'])
        self._msg['dateCreated'] = datetime.strptime(self._msg['dateCreated'][:31], format="%Y-%m-%dT%H:%M:%S.%f")

    @property
    def id(self):
        return self._msg['orderID']

    @property
    def price(self):
        return self._msg['price']

    @property
    def initial_qty(self):
        return self._msg['initialQuantity']

    @property
    def remaining_qty(self):
        return self._msg['quantity']

    @property
    def created_at(self):
        return self._msg['dateCreated']

    @property
    def side(self):
        return self._msg['offerType']

    @property
    def instrument_venue_id(self):
        return self._msg['instrumentID']

    @property
    def status(self):
        return self._msg['status']