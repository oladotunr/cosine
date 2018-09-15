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

    def get(self, key, default=None, split=True):
        parts = key.split(".") if split else [key]
        target = self
        while len(parts) > 0 and target:
            k = parts.pop(0)
            target = getattr(target, k, None)
        return target if target else default


    def __iter__(self):
        return iter(self.__dict__)


    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        raise IndexError("No attribute found at index: "+key)


    def __setitem__(self, key, value):
        setattr(self, key, value)


    def __delitem__(self, key):
        if hasattr(self, key):
            delattr(self, key)
        raise IndexError("No attribute found at index: "+key)


    def keys(self):
        return self.__dict__.keys()


    def asdict(self):
        return self.__dict__


    def items(self):
        return self.__dict__.items()


class Section(FieldSet):
    pass


class Config(Section):

    Section = Section

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    def load(self, file_path=None, stream=None):
        if file_path and os.path.exists(file_path):
            with open(file_path, "r") as fp:
                raw_cfg = yaml.safe_load(fp)
        elif stream:
            raw_cfg = yaml.safe_load(stream)
        else:
            raise ValueError("Config: no source file or stream provided")

        for k in raw_cfg:
            val = Config.cvn(raw_cfg.get(k, self.get(k)))
            setattr(self, k, val)


    def log_config(self, logger):
        logger.info("Config - loaded:")
        def log_attr(k, v, t=None):
            if isinstance(v, Section):
                for (sk, sv) in v.items():
                    log_attr(sk, sv, (t+[k]) if t else [k])
            else:
                k = ".".join(t+[k] if t else [k])
                logger.info(f"Config -     [{k}]: [ {v} ]")
        for (key, val) in self.items():
            log_attr(key, val)


    @staticmethod
    def cvn(a):
        return Section(**{k: Config.cvn(v) for (k, v) in a.items()}) if type(a) is dict else a