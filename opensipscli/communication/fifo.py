#!/usr/bin/env python

import os
import random
import urllib.parse
import urllib.request
from opensipscli.config import cfg
from opensipscli.logger import logger
from opensipscli.communication import jsonrpc_helper

REPLY_FIFO_FILE_TEMPLATE='opensips_fifo_reply_{}'

def execute(method, params):
    jsoncmd = jsonrpc_helper.get_command(method, params)
    reply_fifo_file_name = REPLY_FIFO_FILE_TEMPLATE.format(random.randrange(32767))
    reply_fifo_file = "/tmp/{}".format(reply_fifo_file_name)

    # make sure fifo file does not exist
    try:
        os.unlink(reply_fifo_file)
        logger.debug("removed reply fifo '{}'".format(reply_fifo_file))
    except OSError:
        if os.path.exists(reply_fifo_file):
            raise

    try:
        os.mkfifo(reply_fifo_file)
    except OSError:
        raise

    opensips_fifo = cfg.get('fifo_file')

    fifocmd = ":{}:{}". format(reply_fifo_file_name, jsoncmd)
    with open(opensips_fifo, 'w') as fifo:
        fifo.write(fifocmd)
        logger.debug("sent command '{}'".format(fifocmd))

    with open(reply_fifo_file, 'r') as reply_fifo:
        replycmd = reply_fifo.readline()
        #logger.debug("received reply '{}'".format(replycmd))

    # TODO: should we add this in a loop?
    os.unlink(reply_fifo_file)
    return jsonrpc_helper.get_reply(replycmd)
