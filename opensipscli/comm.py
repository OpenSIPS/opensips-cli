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

from opensipscli.logger import logger
from opensipscli.config import cfg
from opensipscli import communication

comm_handler = None

def initialize():
    global comm_handler
    comm_type = cfg.get('communication_type')
    comm_func = 'opensipscli.communication.{}'.format(comm_type)
    try:
        comm_handler = __import__(comm_func, fromlist=[comm_type])
    except ImportError as ie:
        comm_handler = None
        logger.error("cannot import '{}' handler: {}"
            .format(comm_type, ie))

def execute(cmd, params=[], silent=False):
    global comm_handler
    try:
        ret = comm_handler.execute(cmd, params)
    except communication.jsonrpc_helper.JSONRPCError as ex:
        if not silent:
            logger.error("command '{}' returned: {}".format(cmd, ex))
        return None
    except communication.jsonrpc_helper.JSONRPCException as ex:
        if not silent:
            logger.error("communication exception for '{}' returned: {}".format(cmd, ex))
            logger.error("Is OpenSIPS running?")
        return None
    return ret

def valid():
    global comm_handler
    if not comm_handler:
        return False
    try:
        if hasattr(comm_handler, "valid"):
            return comm_handler.valid()
        return True
    except:
        return False
