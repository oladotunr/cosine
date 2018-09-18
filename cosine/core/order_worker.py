"""
# 
# 15/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
from datetime import datetime, timedelta
from enum import Enum
from decimal import Decimal
from cosine.core.config import FieldSet as Pos
from cosine.core.logger import null_logger
from cosine.core.utils import epsilon_equals
from cosine.core.order_worker_types import PendingAction, LostControlError
from cosine.venues.base_venue import AsyncEvents, OrderType, OfferType, OrderStatus


# MODULE FUNCTIONS
def empty_pos(price=Decimal(0.0)):
    return Pos(
        price=price,
        openpos=Decimal(0.0),
        pending=PendingAction.NONE,
        order=None,
        new_pos=None
    )


# MODULE CLASSES
class CosineOrderWorker(object):

    def __init__(self, active_depth, instrument, venue, logger=None):
        self.logger = logger if logger else null_logger
        self._depth = active_depth
        self._venue = venue
        self._instr = instrument
        self._balances = {}
        self._halted = False
        self._bids = {}
        self._asks = {}
        self._pending_orders = {}
        self._pending_amends = {}
        self._pending_cancels = {}
        self._setup_async()


    def update(self, bids, asks):
        try:
            # reconcile any pending requests...
            self.reconcile()

            # if we're halted then we shouldn't bother doing anything new...
            if self._halted:
                return

            for bid in bids:
                currbid = self._bids.get(bid.price)
                if currbid is None:
                    # new order...
                    self.update_level(OfferType.Bid, bid, empty_pos(price=bid.price))
                elif not epsilon_equals(bid.openpos, currbid.openpos):
                    # update order...
                    self.update_level(OfferType.Bid, bid, currbid)

            # clean up orders...
            new_pxs = map(lambda x: x.price, bids)
            removals = [self._bids[px] for px in self._bids if not px in new_pxs]
            [self.update_level(OfferType.Bid, empty_pos(price=currbid.price), currbid) for currbid in removals]

            for ask in asks:
                currask = self._asks.get(ask.price)
                if currask is None:
                    # new order...
                    self.update_level(OfferType.Ask, ask, empty_pos(price=ask.price))
                elif not epsilon_equals(ask.openpos, currask.openpos):
                    # update order...
                    self.update_level(OfferType.Ask, ask, currask)

            # clean up orders...
            new_pxs = map(lambda x: x.price, asks)
            removals = [self._asks[px] for px in self._asks if not px in new_pxs]
            [self.update_level(OfferType.Ask, empty_pos(price=currask.price), currask) for currask in removals]

        except LostControlError as err:
            self.logger.error(err)
            self.pull_all()


    def pull_all(self):
        self._halted = True
        res = self._venue.cancel_all_orders(instrument=self._instr)
        if not self._venue.is_async:
            self.on_cancel_all_orders(res)


    def update_level(self, side, new_lvl, curr_lvl):
        if curr_lvl.pending != PendingAction.NONE:
            return

        if curr_lvl.openpos == 0.0 and new_lvl.openpos > 0.0 and curr_lvl.order is None and \
           self.check_against_balance(side, price=new_lvl.price, qty=new_lvl.openpos):

            # place a new order...
            self.commit_balance(side, price=new_lvl.price, qty=new_lvl.openpos)
            curr_lvl.pending = PendingAction.NEW_ORDER
            order = self._venue.new_order(
                offer_type=side,
                order_type=OrderType.Limit,
                instrument=self._instr,
                price=new_lvl.price,
                quantity=new_lvl.openpos
            )
            curr_lvl.openpos = order.remaining_qty
            curr_lvl.filled = order.initial_qty - order.remaining_qty
            curr_lvl.pending = PendingAction.from_status(order.status, curr_lvl.pending)
            if curr_lvl.pending != PendingAction.NONE:
                self._pending_orders[order.id] = order
            curr_lvl.order = order

        elif curr_lvl.order and curr_lvl.openpos > 0.0 and new_lvl.openpos == 0.0:

            # clear out the pos...
            curr_lvl.pending = PendingAction.CANCEL_ORDER
            self._pending_cancels[curr_lvl.order.id] = curr_lvl.order
            res = self._venue.cancel_order(curr_lvl.order)
            if not self._venue.is_async:
                self.on_cancel_order(res)

        elif curr_lvl.order:

            # amend the pos...
            curr_lvl.pending = PendingAction.AMEND_ORDER
            curr_lvl.new_pos = new_lvl
            self._pending_amends[curr_lvl.order.id] = curr_lvl.order
            res = self._venue.cancel_order(curr_lvl.order)
            if not self._venue.is_async:
                self.on_cancel_order(res)


    def check_against_balance(self, side, price, qty):
        balance = self._balances[side]
        required = qty if side == OfferType.Ask else price * qty
        available = balance.available_balance
        can_commit = available >= required
        if not can_commit:
            asset = self._instr.asset if side == OfferType.Bid else self._instr.ccy
            self.logger.warning("CosineOrderWorker - [{0}|{1}] Insufficient inventory - (has: {2}, requires: {3})".format(
                self._venue.name,
                asset.symbol,
                available,
                required
            ))
        return can_commit


    def cancel_balance(self, side, price, qty):
        balance = self._balances[side]
        update_value = qty if side == OfferType.Ask else price * qty
        balance.available_balance += update_value


    def clear_balance(self, side, price, qty):
        balance = self._balances[side]
        update_value = qty if side == OfferType.Ask else price * qty
        balance.available_balance -= update_value
        balance.real_balance -= update_value


    def commit_balance(self, side, price, qty):
        balance = self._balances[side]
        update_value = qty if side == OfferType.Ask else price * qty
        balance.available_balance -= update_value


    def balance_sync(self):
        balance_info = self._venue.get_inventory()
        self._balances = {
            OfferType.Ask: balance_info.balances[self._instr.ccy.symbol],
            OfferType.Bid: balance_info.balances[self._instr.asset.symbol]
        }
        self.logger.info(f"CosineOrderWorker - Balances: {self._balances}")


    def synchronise(self):
        # get all the open orders...
        try:
            open_orders = self._venue.get_open_orders(
                instrument=self._instr,
                order_type=OrderType.Limit,
                max_count=self._depth * 2
            )
        except Exception as e:
            self.logger.exception(e)
            raise LostControlError(str("Could not get all open orders for instrument: "+self._instr.name))

        # populate the bids and asks based on the known state at the venue...
        bids = dict(**self._bids)
        asks = dict(**self._asks)
        self._clear_orders()
        for order in open_orders:
            lvls = asks if order.side == OfferType.Ask else bids
            currpos = lvls.get(order.price)
            pos = Pos(
                price=order.price,
                openpos=order.remaining_qty,
                filled=order.initial_qty - order.remaining_qty,
                pending=PendingAction.from_status(order.status, currpos.pending if currpos else PendingAction.NONE),
                order=order
            )
            lvls[order.price] = pos
        self.balance_sync()


    def reconcile(self):
        pendings = len(self._pending_amends) + len(self._pending_orders) + len(self._pending_cancels)
        if pendings == 0:
            return

        # get all the open orders...
        try:
            open_orders = self._venue.get_open_orders(
                instrument=self._instr,
                order_type=OrderType.Limit,
                max_count=self._depth * 2
            )
        except Exception as e:
            self.logger.exception(e)
            raise LostControlError(str("Could not get all open orders for instrument: "+self._instr.name))

        # reconcile any pending states against open positions on the book...
        for order in open_orders:
            lvls = self._asks if order.side == OfferType.Ask else self._bids
            curr_lvl = lvls.get(order.price)
            if not curr_lvl:
                pos = Pos(
                    price=order.price,
                    openpos=order.remaining_qty,
                    filled=order.initial_qty - order.remaining_qty,
                    pending=PendingAction.from_status(order.status, PendingAction.NONE),
                    order=order
                )
                lvls[order.price] = pos
                continue

            if order.status == OrderStatus.Pending:
                continue
            elif curr_lvl.pending == PendingAction.NEW_ORDER:
                curr_lvl.pending = PendingAction.NONE
                curr_lvl.openpos = order.remaining_qty
                curr_lvl.filled = order.initial_qty - order.remaining_qty
                curr_lvl.order = order
                del self._pending_orders[order.id]
            elif curr_lvl.pending == PendingAction.CANCEL_ORDER:
                curr_lvl.pending = PendingAction.NONE
                curr_lvl.openpos = Decimal(0.0)
                curr_lvl.filled = Decimal(0.0)
                curr_lvl.order = None
                del self._pending_cancels[order.id]
            elif curr_lvl.pending == PendingAction.AMEND_ORDER:
                if curr_lvl.new_pos:
                    new_pos = curr_lvl.new_pos
                    self.commit_balance(order.side, price=new_pos.price, qty=new_pos.openpos)
                    curr_lvl.new_pos = None
                    order = self._venue.new_order(
                        offer_type=order.side,
                        order_type=OrderType.Limit,
                        instrument=self._instr,
                        price=new_pos.price,
                        quantity=new_pos.openpos
                    )
                    curr_lvl.openpos = order.remaining_qty
                    curr_lvl.filled = order.initial_qty - order.remaining_qty
                    curr_lvl.pending = PendingAction.from_status(order.status, curr_lvl.pending)
                    curr_lvl.order = order
                else:
                    curr_lvl.pending = PendingAction.NONE
                    curr_lvl.openpos = order.remaining_qty
                    curr_lvl.filled = order.initial_qty - order.remaining_qty
                    curr_lvl.order = order
                    del self._pending_orders[order.id]


    def _setup_async(self):
        if not self._venue.is_async: return
        self._venue.on(AsyncEvents.OnPlaceOrder, self.on_place_order)
        self._venue.on(AsyncEvents.OnExecution, self.on_execution)
        self._venue.on(AsyncEvents.OnCancelOrder, self.on_cancel_order)
        self._venue.on(AsyncEvents.OnCancelAllOrders, self.on_cancel_all_orders)
        try:
            self.synchronise()
        except LostControlError as err:
            self.logger.error(err)
            self.pull_all()


    def _clear_orders(self):
        self._bids.clear()
        self._asks.clear()
        self._pending_orders.clear()
        self._pending_amends.clear()
        self._pending_cancels.clear()


    def on_place_order(self, order):
        if order.placed and order.id in self._pending_orders:
            del self._pending_orders[order.id]
        else:
            raise LostControlError(str(order))


    def on_execution(self, execution):
        if execution.instrument_venue_id != self._instr.venue_id: return

        if execution.price in self._bids:
            bid = self._bids[execution.price]
            if bid.order.id == execution.bid_order_id:
                self.clear_balance(OfferType.Bid, price=execution.price, qty=execution.qty)
                bid.openpos -= execution.qty
                bid.filled += execution.qty
                if bid.openpos == 0.0:
                    del self._bids[execution.price]

        elif execution.price in self._asks:
            ask = self._asks[execution.price]
            if ask.order.id == execution.ask_order_id:
                self.clear_balance(OfferType.Ask, price=execution.price, qty=execution.qty)
                ask.openpos -= execution.qty
                ask.filled += execution.qty
                if ask.openpos == 0.0:
                    del self._asks[execution.price]


    def on_cancel_order(self, response):
        if response.cancelled:
            order = self._pending_cancels.get(response.order_id)
            if order:
                del self._pending_cancels[order.id]
                self.cancel_balance(order.side, price=order.price, qty=order.qty)
        else:
            raise LostControlError(str(response))


    def on_cancel_all_orders(self, response):
        if not response.cancelled:
            raise LostControlError(str(response))
        else:
            self._clear_orders()
            self.balance_sync()


    @property
    def bids(self):
        return self._bids


    @property
    def asks(self):
        return self._asks


    @property
    def instrument(self):
        return self._instr

    @property
    def depth(self):
        return self._depth

