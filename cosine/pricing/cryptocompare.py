"""
# 
# 27/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
import requests
import re

from decimal import Decimal
from socketIO_client import SocketIO
from socketIO_client.transports import get_response, XHR_PollingTransport
from socketIO_client.parsers import get_byte, _read_packet_text, parse_packet_text
from cosine.core.config import FieldSet
from cosine.core.utils import epsilon_equals
from cosine.core.instrument import CosinePairInstrument
from .base_feed import CosineBaseFeed


# rework socket-io protocol to support cryptocompare
# extra function to support XHR1 style protocol
def _new_read_packet_length(content, content_index):
    packet_length_string = ''
    while get_byte(content, content_index) != ord(':'):
        byte = get_byte(content, content_index)
        packet_length_string += chr(byte)
        content_index += 1
    content_index += 1
    return content_index, int(packet_length_string)

def new_decode_engineIO_content(content):
    content_index = 0
    content_length = len(content)
    while content_index < content_length:
        try:
            content_index, packet_length = _new_read_packet_length(
                content, content_index)
        except IndexError:
            break
        content_index, packet_text = _read_packet_text(
            content, content_index, packet_length)
        engineIO_packet_type, engineIO_packet_data = parse_packet_text(
            packet_text)
        yield engineIO_packet_type, engineIO_packet_data

def new_recv_packet(self):
    params = dict(self._params)
    params['t'] = self._get_timestamp()
    response = get_response(
        self.http_session.get,
        self._http_url,
        params=params,
        **self._kw_get)
    for engineIO_packet in new_decode_engineIO_content(response.content):
        engineIO_packet_type, engineIO_packet_data = engineIO_packet
        yield engineIO_packet_type, engineIO_packet_data

setattr(XHR_PollingTransport, 'recv_packet', new_recv_packet)


# MODULE CLASSES
class CryptoCompareSocketIOFeed(CosineBaseFeed):

    FIELDS = {
        'TYPE': 0x0
        , 'MARKET': 0x0
        , 'FROMSYMBOL': 0x0
        , 'TOSYMBOL': 0x0
        , 'FLAGS': 0x0
        , 'PRICE': 0x1
        , 'BID': 0x2
        , 'OFFER': 0x4
        , 'LASTUPDATE': 0x8
        , 'AVG': 0x10
        , 'LASTVOLUME': 0x20
        , 'LASTVOLUMETO': 0x40
        , 'LASTTRADEID': 0x80
        , 'VOLUMEHOUR': 0x100
        , 'VOLUMEHOURTO': 0x200
        , 'VOLUME24HOUR': 0x400
        , 'VOLUME24HOURTO': 0x800
        , 'OPENHOUR': 0x1000
        , 'HIGHHOUR': 0x2000
        , 'LOWHOUR': 0x4000
        , 'OPEN24HOUR': 0x8000
        , 'HIGH24HOUR': 0x10000
        , 'LOW24HOUR': 0x20000
        , 'LASTMARKET': 0x40000
    }

    def __init__(self, name, pool, cxt, logger=None, **kwargs):
        super().__init__(name, pool, cxt, logger=logger, **kwargs)
        self._socketio = None
        self._ticker_map = {}
        self._triangulators = {}


    def _snapshot_cache(self):
        # nothing to do since we'll auto-snapshot on subscription to the websockets feed...
        pass


    def _setup_events(self, worker):
        worker.events.OnRawTick += self._on_raw_tick

    def _process_received_events(self, events, slots):
        # conflate the events to just process for the latest pricing ticks per product...
        evt_group = {}
        icount = len(events)
        for evt in events:
            (name, msg) = evt
            data = self._parse_msg_event(msg)
            if not data: continue
            tkr = str(data["FROMSYMBOL"]) + "/" + str(data["TOSYMBOL"])
            if tkr not in evt_group:
                evt_group[tkr] = evt

        events = [(n, m) for (n, m) in evt_group.items()]
        ecount = len(events)
        if icount != ecount:
            self.logger.info("CryptoCompareSocketIOFeed - Conflated events: {0} / {1}".format(icount, ecount))
        return events


    def _parse_msg_event(self, msg):
        # decode msg...
        fields = msg.split('~')
        try:
            mask = int(fields[-1], 16)
        except:
            self.logger.warn("Failed to decode price feed data: {0}".format(msg))
            return None

        fields = fields[:-1]
        curr = 0
        data = {}
        for prop in self.FIELDS:
            if self.FIELDS[prop] == 0:
                data[prop] = fields[curr]
                curr += 1
            elif mask & self.FIELDS[prop]:
                if prop == 'LASTMARKET':
                    data[prop] = fields[curr]
                else:
                    data[prop] = float(fields[curr])
                    curr += 1
        return data


    def _on_raw_tick(self, msg):
        # decode & cache pricing...
        data = self._parse_msg_event(msg)

        # if it's a triangulated pair then process it separately...
        ticker_pair = str(data["FROMSYMBOL"]) + "/" + str(data["TOSYMBOL"])
        triangulator = self._triangulators.get(ticker_pair)
        if triangulator:
            return self._process_triangulator(trisym=triangulator, subdata=data)

        # if it's a non-triangulated pair then just cache it as-is...
        self._cache_price_data(data=data)

        # fire main tick...
        self._events.OnTick.fire()


    """Worker process run or inline run"""
    def _cache_price_data(self, data):

        instr = str(data["FROMSYMBOL"]) + "/" + str(data["TOSYMBOL"])
        instrument = self._ticker_map[instr]

        if instrument.name in self._cache:
            cached = self._cache[instrument.name]

            moved = cached.midprice
            changed = Decimal(data.get("PRICE", cached.midprice))

            cached.lastmarket = data.get("LASTMARKET", cached.lastmarket)
            cached.midprice = changed
            cached.openhour = Decimal(data.get("OPENHOUR", cached.openhour))
            cached.highhour = Decimal(data.get("HIGHHOUR", cached.highhour))
            cached.lowhour = Decimal(data.get("LOWHOUR", cached.lowhour))
            cached.openday = Decimal(data.get("OPEN24HOUR", cached.openday))
            cached.highday = Decimal(data.get("HIGH24HOUR", cached.highday))
            cached.lowday = Decimal(data.get("LOW24HOUR", cached.lowday))
            cached.lasttradedvol = Decimal(data.get("LASTVOLUME", cached.lasttradedvol))
            cached.lasttradedvolccy = Decimal(data.get("LASTVOLUMETO", cached.lasttradedvolccy))
            cached.dayvol = Decimal(data.get("VOLUME24HOUR", cached.dayvol))
            cached.dayvolccy = Decimal(data.get("VOLUME24HOURTO", cached.dayvolccy))
            return not epsilon_equals(moved, changed)

        return False


    """Worker process run or inline run"""
    def _process_triangulator(self, trisym, subdata):

        # make the request to the triangulator
        try:
            appname = re.sub(r'\s+?', '+', self._cfg.AppName)
            url = f"{self.triangulator}/data/pricemultifull?fsyms={trisym.base}&tsyms={trisym.ccy}&extraParams={appname}"
            response = requests.request('GET', url)
            prices = response.json()["RAW"]
        except Exception as e:
            self.logger.exception(e)
            return

        # triangulate the pricing...
        pxdata = prices[trisym.base][trisym.ccy]
        def triangulate_px(sub, tri, px):
            if px in sub and px in tri:
                sub[px] = Decimal(sub[px]) * Decimal(tri[px])

        triangulate_px(subdata, pxdata, "PRICE")
        triangulate_px(subdata, pxdata, "OPENHOUR")
        triangulate_px(subdata, pxdata, "HIGHHOUR")
        triangulate_px(subdata, pxdata, "LOWHOUR")
        triangulate_px(subdata, pxdata, "OPEN24HOUR")
        triangulate_px(subdata, pxdata, "HIGH24HOUR")
        triangulate_px(subdata, pxdata, "LOW24HOUR")
        triangulate_px(subdata, pxdata, "LASTVOLUME")
        triangulate_px(subdata, pxdata, "LASTVOLUMETO")
        triangulate_px(subdata, pxdata, "VOLUME24HOUR")
        triangulate_px(subdata, pxdata, "VOLUME24HOURTO")
        subdata["TOSYMBOL"] = pxdata["TOSYMBOL"]

        # update the cache and fire the tick event if the prices have moved...
        moved = True
        moved &= self._cache_price_data(data=subdata)

        if not moved:
            return

        # fire main tick...
        self._events.OnTick.fire()


    """Worker process run or inline run"""
    def run(self):
        self._setup()
        self._listen()


    """Worker process run or inline run"""
    def _setup(self):

        # establish the connection...
        self.logger.info(f"CryptoCompareSocketIOFeed - Establishing connection: {self.endpoint} ({self.port})")
        self._socketio = SocketIO(self.endpoint, port=self.port)
        self.logger.info(f"CryptoCompareSocketIOFeed - Connection established")

        # subscribe for all instruments...
        subs = []
        for n in self._cache:
            instrument = self._cache[n].instrument
            if not isinstance(instrument, CosinePairInstrument): continue

            # handle any ticker remapping required for this pricing feed...
            feed_data = instrument.symbology.attrs.get(self._feed_name, {})
            ticker = feed_data.get('Ticker', instrument.asset.symbol)
            ccy_ticker = feed_data.get('TickerCCY', instrument.ccy.symbol)
            ticker_pair = ticker+'/'+ccy_ticker
            self._ticker_map[ticker_pair] = instrument

            # handle any triangulation via a base currency required...
            ccy_base = feed_data.get('BaseCCY')
            if ccy_base:
                ticker_base_pair = ticker + '/' + ccy_base
                self._triangulators[ticker_base_pair] = FieldSet(base=ccy_base, origin=ticker, ccy=ccy_ticker, instr=instrument)
                ccy_ticker = ccy_base

            # now add the ticker for subscription...
            self.logger.info(f"CryptoCompareSocketIOFeed - Subscribing for instrument: {instrument.symbol} (via {ticker}/{ccy_ticker})")
            subs.append('5~CCCAGG~{0}~{1}'.format(ticker, ccy_ticker))

        self._socketio.emit('SubAdd', {"subs": subs})
        self._socketio.on('m', self._on_sio_tick)


    """Worker process run or inline run"""
    def _listen(self):
        self._socketio.wait()


    """Worker process run or inline run"""
    def _on_sio_tick(self, message):
        self.logger.debug(f"CryptoCompareSocketIOFeed - On Tick: {str(message)}")
        if self._worker:
            self._worker.enqueue_event("OnRawTick", message)
        else:
            self._on_raw_tick(message)

