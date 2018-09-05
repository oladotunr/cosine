"""
# 
# 15/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS



# MODULE CLASSES
class CosineBaseStrategy(object):

    def __init__(self, cfg, cxt, venues, pool, **kwargs):
        [setattr(self, k, kwargs[k]) for k in kwargs]
        self._cfg = cfg
        self._cxt = cxt
        self._venues = venues
        self._pool = pool


    def setup(self):
        pass


    def teardown(self):
        pass


    def update(self):
        raise NotImplementedError()

