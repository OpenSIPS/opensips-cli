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
from opensips.mi import OpenSIPSMI, OpenSIPSMIException

comm_handler = None
comm_handler_valid = None

def initialize():
    global comm_handler
    comm_type = cfg.get('communication_type')
    comm_handler = OpenSIPSMI(comm_type, **cfg.to_dict())
    valid()

def execute(cmd, params=[], silent=False):
    global comm_handler
    try:
        ret = comm_handler.execute(cmd, params)
    except OpenSIPSMIException as ex:
        if not silent:
            logger.error("command '{}' returned: {}".format(cmd, ex))
        return None
    return ret

def valid():
    global comm_handler
    global comm_handler_valid
    if comm_handler_valid:
        return comm_handler_valid
    if not comm_handler:
        comm_handler_valid = (False, None)
    try:
        if hasattr(comm_handler, "valid"):
            comm_handler_valid = comm_handler.valid()
        else:
            comm_handler_valid = (True, None)
    except:
        comm_handler_valid = (False, None)
    return comm_handler_valid
