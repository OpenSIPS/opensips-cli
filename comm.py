#!/usr/bin/env python3

import communication
from cli import *
from logger import logger
from config import cfg

comm_handler = None

def initialize():
    global comm_handler
    comm_type = cfg.get('comm_type')
    comm_func = 'communication.opensipsctl_{}'.format(comm_type)
    try:
        comm_handler = __import__(comm_func)
    except ImportError as ie:
        comm_handler = None
        logger.error("cannot import '{}' handler: {}"
            .format(comm_type, ie))

def execute(cmd, params=[]):
    global comm_handler
    return comm_handler.execute(cmd, params)

