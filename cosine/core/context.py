"""
# 
# 15/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
from cosine.core.utils import find_instrument


# MODULE CLASSES
class CosineCoreContext(object):

    def __init__(self):
        self.feeds = None
        self.pricers = None
        self.pricer_seq = None
        self.strategy = None
        self.orders = None
        self.instruments = {}


    def find_instrument(self, term):
        return find_instrument(self.instruments, term=term)