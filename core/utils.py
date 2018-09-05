"""
# 
# 26/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
import inspect
import importlib

from sys import float_info as flt
from threading import Timer


# FUNCTIONS
def epsilon_equals(x, y):
    return abs(x - y) <= flt.epsilon


# DECORATORS
def debounce(wait):
    """ Decorator that will postpone a functions
        execution until after wait seconds
        have elapsed since the last time it was invoked. """
    def decorator(fn):
        def debounced(*args, **kwargs):
            def call_it():
                fn(*args, **kwargs)
            try:
                debounced.t.cancel()
            except AttributeError:
                pass
            debounced.t = Timer(wait, call_it)
            debounced.t.start()
        return debounced
    return decorator

def collate_classes(BaseClass):
    def collator(modules):
        classes = {}
        for m in modules:
            pkg = None
            if isinstance(m, (tuple, list)):
                (m, pkg) = m
            module = importlib.import_module(m, package=pkg)
            clsmembers = [
                cls for cls in inspect.getmembers(module, inspect.isclass) if isinstance(cls, type) and issubclass(cls, BaseClass)
            ]
            if len(clsmembers) > 0:
                classes[m] = clsmembers[0]
        return classes
    return collator

def locate_class(BaseClass):
    def locator(module_name, pkg=None):
        module = importlib.import_module(module_name, package=pkg)
        clsmembers = [
            cls for cls in inspect.getmembers(module, inspect.isclass) if isinstance(cls, type) and issubclass(cls, BaseClass)
        ]
        return clsmembers[0] if len(clsmembers) > 0 else None
    return locator


# MODULE CLASSES
class CosineEventSlot(object):
    def __init__(self):
        self._handlers = []

    def __iadd__(self, handler):
        self._handlers.append(handler)
        return self

    def __isub__(self, handler):
        self._handlers.remove(handler)
        return self

    async def fire(self, *args, **kwargs):
        for handler in self._handlers:
            handler(*args, **kwargs)