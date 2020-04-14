#!/usr/bin/env python
##
## This file is part of OpenSIPS CLI
## (see https://github.com/OpenSIPS/opensips-cli).
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program. If not, see <http://www.gnu.org/licenses/>.
##

import os
import stat
import random
from opensipscli.config import cfg
from opensipscli.logger import logger
from opensipscli.communication import jsonrpc_helper

REPLY_FIFO_FILE_TEMPLATE='opensips_fifo_reply_{}'

def execute(method, params):
    jsoncmd = jsonrpc_helper.get_command(method, params)
    reply_fifo_file_name = REPLY_FIFO_FILE_TEMPLATE.format(random.randrange(32767))
    reply_dir = cfg.get('fifo_reply_dir')
    reply_fifo_file = "{}/{}".format(reply_dir, reply_fifo_file_name)

    # make sure fifo file does not exist
    try:
        os.unlink(reply_fifo_file)
        logger.debug("removed reply fifo '{}'".format(reply_fifo_file))
    except OSError as ex:
        if os.path.exists(reply_fifo_file):
            raise jsonrpc_helper.JSONRPCException(
                    "cannot remove repl file {}: {}!".
                    format(reply_fifo_file, ex))

    try:
        os.mkfifo(reply_fifo_file)
        os.chmod(reply_fifo_file, 0o666)
    except OSError as ex:
        raise jsonrpc_helper.JSONRPCException(
                "cannot create reply file {}: {}!".
                format(reply_fifo_file, ex))

    opensips_fifo = cfg.get('fifo_file')
    if not os.path.exists(opensips_fifo):
        raise jsonrpc_helper.JSONRPCException(
                "fifo file {} does not exist!".
                format(opensips_fifo))

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

def valid():
    opensips_fifo = cfg.get('fifo_file')
    if not os.path.exists(opensips_fifo):
        logger.debug("fifo file {} does not exist!".format(opensips_fifo))
        return False
    return True
