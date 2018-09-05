"""
# 
# 03/09/2018
# Oladotun Rominiyi - Copyright © 2018. all rights reserved.
"""
__author__ = 'dotun rominiyi'

# IMPORTS
from recommonmark.parser import CommonMarkParser


# MODULE VARS
source_parsers = {
    '.md': CommonMarkParser,
}

source_suffix = ['.rst', '.md']