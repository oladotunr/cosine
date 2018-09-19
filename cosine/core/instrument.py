"""
# 
# 21/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
import sys
import inspect

from cosine.core.tradeable import CosineTradableAsset, CosineSymbology


# MODULE CLASSES
class CosineInstrument(CosineTradableAsset):

    def __init__(self, cache=None, **kwargs):
        self._name = kwargs["name"]
        self._category = kwargs["category"]
        self._type = kwargs["type"]
        self._precision = kwargs["precision"]
        self._symbology = CosineSymbology(kwargs, **kwargs["symbology"])
        if cache:
            cache[self.symbol] = self


    @staticmethod
    def load(cache, **instr_def):
        if instr_def['symbol'] in cache:
            return cache[instr_def['symbol']]

        if not ("_instr_classes" in cache):
            current_module = sys.modules[__name__]
            instrument_classes = current_module.__dict__
            cache["_instr_classes"] = instrument_classes
        else:
            instrument_classes = cache["_instr_classes"]

        InstrumentClass = instrument_classes[instr_def.get("cls", "CosineInstrument")]
        return InstrumentClass(cache=cache, **instr_def)



class CosinePairInstrument(CosineTradableAsset):

    def __init__(self, cache=None, **kwargs):

        asset = CosineInstrument.load(cache=cache, **kwargs["asset"])
        quote_ccy = CosineInstrument.load(cache=cache, **kwargs["quote_ccy"])

        self._asset = asset
        self._quote_ccy = quote_ccy
        self._name = asset.symbol + "/" + quote_ccy.symbol
        self._base_name = kwargs["name"]
        self._category = kwargs["category"]
        self._type = kwargs["type"]
        self._precision = kwargs["precision"]
        self._symbology = CosineSymbology(kwargs, **kwargs["symbology"])
        self._symbology.attrs["base_name"] = self._base_name
        self._symbology.attrs["name"] = self._name
        self._symbology.venue_id = kwargs.get('venue_id')
        if cache:
            cache[self.symbol] = self


    @property
    def asset(self):
        return self._asset

    @property
    def ccy(self):
        return self._quote_ccy
