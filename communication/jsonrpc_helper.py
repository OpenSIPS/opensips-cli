#!/usr/bin/env python

import json
from random import randint

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
        return '{}: {}'.format(self.code, self.data)

def get_command(method, params={}):
    cmd = {
            'jsonrpc': '2.0',
            'id': str(randint(0, 32767)),
            'method': method,
            'params': params
    };
    return json.dumps(cmd);

def get_reply(cmd):
    try:
        j = json.loads(cmd)
        if 'error' in j and j['error'] is not None:
            error = j['error']
            raise JSONRPCError(j['error']['code'], j['error']['message'])
        elif not 'result' in j:
            raise JSONRPCError(-32603, 'Internal error')
        else:
            return j['result']
    except json.decoder.JSONDecodeError:
        raise JSONRPCException

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

