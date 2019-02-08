#!/usr/bin/env python

from opensipscli.logger import logger
from opensipscli.config import cfg
from opensipscli import communication

comm_handler = None

def initialize():
    global comm_handler
    comm_type = cfg.get('comm_type')
    comm_func = 'opensipscli.communication.{}'.format(comm_type)
    try:
        comm_handler = __import__(comm_func, fromlist=[comm_type])
    except ImportError as ie:
        comm_handler = None
        logger.error("cannot import '{}' handler: {}"
            .format(comm_type, ie))

def execute(cmd, params=[]):
    global comm_handler
    try:
        ret = comm_handler.execute(cmd, params)
    except communication.jsonrpc_helper.JSONRPCError as ex:
        logger.error("command '{}' returned {}".format(cmd, ex))
        return None
    return ret

