"""
# 
# 09/09/2018
# BlockEx - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
from unittest import TestCase
from cosine.core.utils import collate_classes
from cosine.venues.base_venue import CosineBaseVenue


# MODULE CLASSES
class ClassQueriesTest(TestCase):

    def test_collate_classes(self):

        venue_finder = collate_classes(CosineBaseVenue)
        venues = venue_finder(modules=["cosine.venues.bem"])
        self.assertIsInstance(venues, dict)
        self.assertGreater(len(venues.keys()), 0)
        VenueClass = venues['cosine.venues.bem']
        self.assertIsInstance(VenueClass, type)
        self.assertTrue(issubclass(VenueClass, CosineBaseVenue) and VenueClass is not CosineBaseVenue)
        self.assertEqual(VenueClass.__name__, "BlockExMarketsVenue")
