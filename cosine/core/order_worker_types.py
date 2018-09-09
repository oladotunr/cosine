"""
# 
# 09/09/2018
# BlockEx - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
from enum import Enum
from cosine.venues.base_venue import OrderStatus


# MODULE CLASSES
class LostControlError(Exception):
    pass


class PendingAction(Enum):
    NONE                = 0
    NEW_ORDER           = 1
    AMEND_ORDER         = 2
    CANCEL_ORDER        = 3
    CANCEL_ALL          = 4

    @classmethod
    def from_status(cls, status, prev_pending):
        if prev_pending is cls.NONE:
            return {
                OrderStatus.Pending: cls.NEW_ORDER
            }.get(status, cls.NONE)
        else:
            return prev_pending