"""
# 
# 21/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS



# MODULE CLASSES
class CosineTradableAsset(object):

    @property
    def name(self):
        return self._name

    @property
    def category(self):
        return self._category

    @property
    def type(self):
        return self._type

    @property
    def precision(self):
        return self._precision

    @property
    def symbol(self):
        return self._symbology.symbol

    @property
    def symbology(self):
        return self._symbology

    @property
    def venue_id(self):
        return self._symbology.venue_id


class CosineSymbology:

    def __init__(self, instr_attrs, **kwargs):
        [setattr(self, k, kwargs[k]) for k in kwargs]
        self.attrs = instr_attrs


    def match(self, term):
        for attr in self.attrs.values():
            if type(term) is type(attr) and term == attr:
                return True

        for k, v in self.__dict__.items():
            if k == 'attrs': continue
            if type(term) is type(v) and term == v:
                return True
        return False


    def match_in(self, terms):
        for term in terms:
            if self.match(term=term):
                return True
        return False


    @staticmethod
    def match_for(symdata, term):
        if isinstance(symdata, object) and not isinstance(symdata, dict):
            symdata = symdata.__dict__

        for k, v in symdata:
            if isinstance(v, (object, dict)):
                if CosineSymbology.match_for(v, term=term):
                    return True
                else:
                    continue

            if type(term) is type(v) and term == v:
                return True
        return False

    @staticmethod
    def match_for_all(symdata, terms):
        for term in terms:
            if CosineSymbology.match(symdata, term=term):
                return True
        return False