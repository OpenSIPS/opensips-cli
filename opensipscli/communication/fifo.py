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
import errno
import random
from opensipscli.config import cfg
from opensipscli.logger import logger
from opensipscli.communication import jsonrpc_helper

REPLY_FIFO_FILE_TEMPLATE='opensips_fifo_reply_{}'
fifo_file = None

def get_sticky(path):
    if path == '/':
        return None
    if os.stat(path).st_mode & 0o1000 == 0o1000:
        return path
    return get_sticky(os.path.split(path)[0])

def execute(method, params):
    global fifo_file

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

    fifocmd = ":{}:{}". format(reply_fifo_file_name, jsoncmd)
    try:
        fifo = open(fifo_file, 'w')
        fifo.write(fifocmd)
        logger.debug("sent command '{}'".format(fifocmd))
        fifo.close()
    except Exception as ex:
        raise jsonrpc_helper.JSONRPCException(
                "cannot access fifo file {}: {}!".
                format(fifo_file, ex))

    logger.debug("reply file '{}'".format(reply_fifo_file))
    with open(reply_fifo_file, 'r', errors='replace') as reply_fifo:
        replycmd = reply_fifo.readline()
        #logger.debug("received reply '{}'".format(replycmd))

    # TODO: should we add this in a loop?
    os.unlink(reply_fifo_file)
    return jsonrpc_helper.get_reply(replycmd)

def valid():
    global fifo_file

    opensips_fifo = cfg.get('fifo_file')
    if not os.path.exists(opensips_fifo):
        opensips_fifo_bk = opensips_fifo
        opensips_fifo = cfg.get('fifo_file_fallback')
        if not opensips_fifo or not os.path.exists(opensips_fifo):
            msg = "fifo file {} does not exist!".format(opensips_fifo)
            logger.debug(msg)
            return (False, [msg, 'Is OpenSIPS running?'])
        logger.debug("switched fifo from '{}' to fallback '{}'".
                format(opensips_fifo_bk, opensips_fifo))

    try:
        open(opensips_fifo, 'w').close()
    except OSError as ex:
        extra = []
        if ex.errno == errno.EACCES:
            sticky = get_sticky(os.path.dirname(opensips_fifo))
            if sticky:
                extra = ["starting with Linux kernel 4.19, processes can " +
                        "no longer read from FIFO files ",
                        "that are saved in directories with sticky " +
                        "bits (such as {})".format(sticky),
                        "and are not owned by the same user the " +
                        "process runs with. ",
                        "To fix this, either store the file in a non-sticky " +
                        "bit directory (such as /var/run/opensips), ",
                        "or disable fifo file protection using " +
                        "'sysctl fs.protected_fifos=0' (NOT RECOMMENDED)"]

        msg = "cannot access fifo file {}: {}".format(opensips_fifo, ex)
        logger.debug(msg)
        return (False, [msg] + extra)
    fifo_file = opensips_fifo
    return (True, None)
