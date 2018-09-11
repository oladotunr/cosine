"""
# 
# 30/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
from .base_pricer import CosinePricer


# MODULE CLASSES
class NullPricer(CosinePricer):

    def __init__(self, name, pool, cxt, logger=None, **kwargs):
        super().__init__(name, pool, cxt, logger=logger, **kwargs)


    def setup(self):
        pass


    def teardown(self):
        pass


    def generate_theo_prices(self, instrument_prices):
        return instrument_prices
