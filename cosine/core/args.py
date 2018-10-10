"""
# 
# 10/10/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
import argparse


# MODULE CLASSES
class CosineCmdLineArgs(object):

    def __init__(self, appdesc, capture_args=None):

        # create the parser and add capturing for required arguments...
        self.parser = argparse.ArgumentParser(description=appdesc)
        self.parser.add_argument("-c", "--config",
                                 help="Config YAML file required to setup the algo.")
        self.parser.add_argument("-e", "--env", choices=['DEV', 'TST', 'PRD'],
                                 help="The execution environment.")
        self.parser.add_argument("-a", "--appname", default=appdesc,
                                 help="The name of the application.")
        self.parser.add_argument("-lf", "--logfile",
                                 help="The name of the log file. Do not change this unless you know what you're doing.")
        self.parser.add_argument("-lv", "--loglevel",
                                 choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'FATAL', 'CRITICAL'],
                                 help="Log level.")
        self.parser.add_argument("-nl", "--nologfile",
                                 const=True, default=False, nargs='?',
                                 help="Disable log file generation.")

        # add any custom arguments...
        for (args, kwargs) in (capture_args if capture_args else []):
            self.parser.add_argument(*args, **kwargs)

        # init the args object...
        self.args = None


    def print_help(self):
        self.parser.print_help()


    def parse(self):
        self.args = self.parser.parse_args()

        # filter out None value fields...
        self.args = self.args.__class__(**({arg: self.args.__dict__[arg] for arg in self.args.__dict__ if self.args.__dict__[arg] is not None}))
        return self.args


    def get(self):
        return self.args


    def asdict(self):
        return self.args.__dict__ if self.args else {}
