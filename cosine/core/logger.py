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
    log_level = logging._nameToLevel[ args.get("loglevel", os.environ.get("COSINE_LOGLVL", "INFO")) ]
    no_log_file = args.get("nologfile", os.environ.get("COSINE_NOLOGFILE") == "Y")

    # create the logger...
    _logger = logging.getLogger(appname)
    _logger.setLevel(log_level)
    formatter = logging.Formatter('[%(asctime)s][%(thread)d][%(levelname)s]: %(message)s')

    # add a file handler...
    if not no_log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        _logger.addHandler(fh)

    # add a stream handler...
    sh = logging.StreamHandler()
    sh.setLevel(log_level)
    sh.setFormatter(formatter)
    _logger.addHandler(sh)

    # set the logger to module scope variable for universal access...
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