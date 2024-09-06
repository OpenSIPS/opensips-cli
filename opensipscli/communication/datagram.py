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

import urllib.request
from opensipscli.logger import logger
from opensipscli.config import cfg
from opensipscli.communication import jsonrpc_helper
import socket

def execute(method, params):
    ip = cfg.get('datagram_ip')
    port = int(cfg.get('datagram_port'))
    jsoncmd = jsonrpc_helper.get_command(method, params)
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        udp_socket.sendto(jsoncmd.encode(), (ip, port))
        udp_socket.settimeout(5.0)
        replycmd = udp_socket.recv(1024)
    except Exception as e:
        raise jsonrpc_helper.JSONRPCException(e)
    finally:
        udp_socket.close()
    return jsonrpc_helper.get_reply(replycmd)

def valid():
    return (True, None)
