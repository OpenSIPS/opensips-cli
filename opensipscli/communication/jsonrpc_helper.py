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

import json
from random import randint
from collections import OrderedDict

try:
    from json.decoder import JSONDecodeError
except ImportError: # JSONDecodeError is not available in  python3.4
    JSONDecodeError = ValueError

"""
This function contains helper functions to build and parse JSONRPC commands
"""

class JSONRPCException(Exception):
    pass

class JSONRPCError(JSONRPCException):

    def __init__(self, code, message, data=None):
        self.code = code
        self.message = message
        self.data = data

    def get_data(self):
        return self.data

    def __str__(self):
        return '{}: {}'.format(self.code, self.message)

def get_command(method, params={}):
    cmd = {
            'jsonrpc': '2.0',
            'id': str(randint(0, 32767)),
            'method': method,
            'params': params
    }
    return json.dumps(cmd)

def get_reply(cmd):
    try:
        j = json.loads(cmd, object_pairs_hook=OrderedDict)
        if 'error' in j and j['error'] is not None:
            error = j['error']
            raise JSONRPCError(j['error']['code'], j['error']['message'])
        elif not 'result' in j:
            raise JSONRPCError(-32603, 'Internal error')
        else:
            return j['result']
    except JSONDecodeError:
        raise JSONRPCException

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

