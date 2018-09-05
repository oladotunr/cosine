"""
# 
# 21/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
from unittest import TestCase
from io import StringIO
from cosine.core.config import Config


# MODULE CLASSES
class ConfigTest(TestCase):

    TESTFILEA = "a:\n    i: 1\n    j: 20.0\n    k: false\n"

    def test_load(self):
        cfg = Config()
        cfg.load(stream=StringIO(ConfigTest.TESTFILEA))
        self.assertIn("a", cfg)
        self.assertIs(type(cfg.a), Config.Section)
        self.assertIn("i", cfg.a)
        self.assertIn("j", cfg.a)
        self.assertIn("k", cfg.a)
        self.assertIs(type(cfg.a.i), int)
        self.assertIs(type(cfg.a.j), float)
        self.assertIs(type(cfg.a.k), bool)
