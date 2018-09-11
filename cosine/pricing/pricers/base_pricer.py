"""
# 
# 30/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
from cosine.core.logger import null_logger


# MODULE CLASSES
class CosinePricer(object):

    def __init__(self, name, pool, cxt, logger=None, **kwargs):
        [setattr(self, k, kwargs[k]) for k in kwargs]
        self.logger = logger if logger else null_logger
        self.name = name
        self._pool = pool
        self._cxt = cxt


    def setup(self):
        raise NotImplementedError()


    def teardown(self):
        raise NotImplementedError()


    def generate_theo_prices(self, instrument_prices):
        raise NotImplementedError()
