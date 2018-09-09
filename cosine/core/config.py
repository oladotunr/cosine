"""
# 
# 15/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
import os
import io
import yaml
from argparse import Namespace


# MODULE CLASSES
class FieldSet(Namespace):

    def get(self, key, default=None):
        return getattr(self, key, default)


    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        raise IndexError("No attribute found at index: "+key)



class Section(FieldSet):
    pass


class Config(Section):

    Section = Section

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    def load(self, file_path=None, stream=None):

        if file_path:
            with open(file_path, "r") as fp:
                raw_cfg = yaml.safe_load(fp)
        elif stream:
            raw_cfg = yaml.safe_load(stream)
        else:
            raise ValueError("Config: no source file or stream provided")

        for k in raw_cfg:
            val = Config.cvn(raw_cfg.get(k, getattr(self, k)))
            setattr(self, k, val)


    @staticmethod
    def cvn(a):
        return Section(**{k: Config.cvn(v) for (k, v) in a.items()}) if type(a) is dict else a