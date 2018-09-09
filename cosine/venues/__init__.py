"""
# 
# 15/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
from cosine.core.utils import collate_classes
from .base_venue import CosineBaseVenue


# MODULE CLASSES
def collate_venues(modules):
    return collate_classes(CosineBaseVenue)(modules)
