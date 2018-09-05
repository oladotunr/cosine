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
        return self._symbology.base_symbol

    @property
    def symbology(self):
        return self._symbology


class CosineSymbology:

    def __init__(self, instr_attrs, **kwargs):
        [setattr(self, k, kwargs[k]) for k in kwargs]
        self.attrs = instr_attrs