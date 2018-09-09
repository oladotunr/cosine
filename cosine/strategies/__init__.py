"""
# 
# 15/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
from cosine.core.utils import locate_class
from .base_strategy import CosineBaseStrategy


# MODULE CLASSES
def locate_strategy(module_name):
    return locate_class(CosineBaseStrategy)(module_name)
