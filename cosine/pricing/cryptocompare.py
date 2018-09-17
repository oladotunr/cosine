"""
# 
# 27/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
from decimal import Decimal
from socketIO_client import SocketIO
from socketIO_client.transports import get_response, XHR_PollingTransport
from socketIO_client.parsers import get_byte, _read_packet_text, parse_packet_text
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

    def __init__(self, name, pool, cxt, logger=None, **kwargs):
        super().__init__(name, pool, cxt, logger=logger, **kwargs)
        self._socketio = None
        self._ticker_map = {}


    def _snapshot_cache(self):
        # nothing to do since we'll auto-snapshot on subscription to the websockets feed...
        pass


    def _setup_events(self, worker):
        worker.events.OnRawTick += self._on_raw_tick


    def _on_raw_tick(self, msg):
        # decode & cache pricing...
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
        fields = msg.split('~')
        try:
            mask = int(fields[-1], 16)
        except:
            self.logger.warn("Failed to decode price feed data: {0}".format(msg))
            return
        fields = fields[:-1]
        curr = 0
        data = {}
        for prop in FIELDS:
            if FIELDS[prop] == 0:
                data[prop] = fields[curr]
                curr += 1
            elif mask & FIELDS[prop]:
                if prop == 'LASTMARKET':
                    data[prop] = fields[curr]
                else:
                    data[prop] = float(fields[curr])
                    curr += 1

        instr = str(data["FROMSYMBOL"]) + "/" + str(data["TOSYMBOL"])
        instrument = self._ticker_map[instr]
        if instrument.name in self._cache:
            cached = self._cache[instrument.name]
            cached.lastmarket = data.get("LASTMARKET", cached.lastmarket)
            cached.midprice = Decimal(data.get("PRICE", cached.midprice))
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
            self._ticker_map[ticker+'/'+instrument.ccy.symbol] = instrument

            # handle any triangulation via a base currency required...

            # now add the ticker for subscription...
            self.logger.info(f"CryptoCompareSocketIOFeed - Subscribing for instrument: {instrument.symbol} (via {ticker})")
            subs.append('5~CCCAGG~{0}~{1}'.format(ticker, instrument.ccy.symbol))

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

