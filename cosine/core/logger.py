"""
# 
# 25/08/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
import os
import logging


# MODULE LOGGER
logger = None

# MODULE FUNCTIONS
def create_logger(args):
    appname = args.get("appname", os.environ.get("COSINE_APP", "cosine"))
    env = args.get("env", os.environ.get("COSINE_ENV", "DEV"))
    log_file = args.get("logfile", os.environ.get("COSINE_LOGFILE", "{0}.{1}.{2}.log".format(appname, env, os.getpid())))
    log_level = args.get("loglevel", os.environ.get("COSINE_LOGLVL", "INFO"))

    _logger = logging.getLogger(appname)
    _logger.setLevel(logging._nameToLevel[log_level])
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging._nameToLevel[log_level])
    formatter = logging.Formatter('[%(asctime)s][%(thread)d][%(levelname)s]: %(message)s')
    fh.setFormatter(formatter)
    _logger.addHandler(fh)
    globals()["logger"] = _logger
    return _logger

# MODULE CLASSES
class NullLogger(object):

    def debug(self, *args, **kwargs):
        pass

    def info(self, *args, **kwargs):
        pass

    def warn(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass

    def critical(self, *args, **kwargs):
        pass

    def fatal(self, *args, **kwargs):
        pass


null_logger = NullLogger()