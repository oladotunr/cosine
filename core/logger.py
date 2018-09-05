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

# MODULE CLASSES
def create_logger(args):
    appname = os.environ.get("COSINE_APP", args.get("appname", "cosine"))
    env = os.environ.get("COSINE_ENV", args.get("env", "DEV"))
    log_file = os.environ.get("COSINE_LOGFILE", args.get("logfile", "{0}.{1}.{2}.log".format(appname, env, os.getpid())))
    log_level = os.environ.get("COSINE_LOGLVL", args.get("loglevel", "INFO"))

    _logger = logging.getLogger(appname)
    _logger.setLevel(logging._nameToLevel[log_level])
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging._nameToLevel[log_level])
    formatter = logging.Formatter('[%(asctime)s][%(thread)d][%(levelname)s]: %(message)s')
    fh.setFormatter(formatter)
    _logger.addHandler(fh)
    globals()["logger"] = _logger
    return _logger
