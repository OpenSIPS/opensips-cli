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

import socket
import urllib.parse
import urllib.request
from opensipscli.config import cfg
from opensipscli.communication import jsonrpc_helper

def execute(method, params):
    url = cfg.get('url')
    jsoncmd = jsonrpc_helper.get_command(method, params)
    headers = { 'Content-Type': 'application/json' }
    request = urllib.request.Request(url,
            jsoncmd.encode(), headers)
    replycmd = urllib.request.urlopen(request).read().decode()
    return jsonrpc_helper.get_reply(replycmd)

def valid():
    # check to see if there is an open connection
    url = cfg.get('url')
    try:
        url_parsed = urllib.parse.urlparse(url)
        if not url_parsed.port:
            if url_parsed.scheme == 'http':
                url_parsed.port = 80
            else:
                url_parsed.port = 443
        s = socket.socket()
        s.connect((url_parsed.hostname, url_parsed.port))
        s.close()
        return True
    except Exception as e:
        logger.debug("could not connect to {} ({})".format(url, e))
        return False
    return False

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
