"""
# 
# 15/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
from cosine.core.utils import collate_classes, locate_class
from .base_feed import CosineBaseFeed
from .pricers.base_pricer import CosinePricer


# MODULE CLASSES
def collate_feeds(modules):
    return collate_classes(CosineBaseFeed)(modules)

def collate_pricers(modules):
    return collate_classes(CosinePricer)(modules)

def locate_pricer(module_name):
    return locate_class(CosinePricer)(module_name)
