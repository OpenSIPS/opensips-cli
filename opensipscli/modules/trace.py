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

from datetime import datetime
from time import time
import random
import socket
from opensipscli import comm
from opensipscli.config import cfg
from opensipscli.logger import logger
from opensipscli.module import Module

TRACE_BUFFER_SIZE = 65535

'''
find out more information here:
* https://github.com/sipcapture/HEP/blob/master/docs/HEP3NetworkProtocolSpecification_REV26.pdf
'''

protocol_types = {
    0x00: "UNKNOWN",
    0x01: "SIP",
    0x02: "XMPP",
    0x03: "SDP",
    0x04: "RTP",
    0x05: "RTCP JSON",
    0x56: "LOG",
    0x57: "MI",
    0x58: "REST",
    0x59: "NET",
    0x60: "CONTROL",
}

protocol_ids = {
    num:name[8:] for name,num in vars(socket).items() if name.startswith("IPPROTO")
}

class HEPpacketException(Exception):
    pass

class HEPpacket(object):

    def __init__(self, payloads):
        self.payloads = payloads
        self.family = socket.AF_INET
        self.protocol = "UNKNOWN"
        self.src_addr = None
        self.dst_addr = None
        self.src_port = None
        self.dst_port = None
        self.data = None
        self.correlation = None
        self.ts = time()
        self.tms = datetime.now().microsecond

    def __str__(self):
        time_str = "{}.{}".format(
                self.ts,
                self.tms)
        protocol_str = " {}/{}".format(
                self.protocol,
                self.type)

        if self.type == "SIP":
            ip_str = " {}:{} -> {}:{}".format(
                socket.inet_ntop(self.family, self.src_addr),
                self.src_port,
                socket.inet_ntop(self.family, self.dst_addr),
                self.dst_port)
        else:
            ip_str = ""
        if self.data:
            data_str = self.data.decode()
        else:
            data_str = ""

        return logger.color(logger.BLUE, time_str) + \
                logger.color(logger.CYAN, protocol_str + ip_str) + \
                "\n" + data_str

    def parse(self):
        length = len(self.payloads)
        payloads = self.payloads
        while length > 0:
            if length < 6:
                logger.error("payload too small {}".format(length))
                return None
            chunk_vendor_id = int.from_bytes(payloads[0:2],
                    byteorder="big", signed=False)
            chunk_type_id = int.from_bytes(payloads[2:4],
                    byteorder="big", signed=False)
            chunk_len = int.from_bytes(payloads[4:6],
                    byteorder="big", signed=False)
            if chunk_len < 6:
                logger.error("chunk too small {}".format(chunk_len))
                return None
            payload = payloads[6:chunk_len]
            payloads = payloads[chunk_len:]
            length = length - chunk_len
            self.push_chunk(chunk_vendor_id, chunk_type_id, payload)

    def push_chunk(self, vendor_id, type_id, payload):

        if vendor_id != 0:
            logger.warning("Unknown vendor id {}".format(vendor_id))
            raise HEPpacketException
        if type_id == 0x0001:
            if len(payload) != 1:
                raise HEPpacketException
            self.family = payload[0]
        elif type_id == 0x0002:
            if len(payload) != 1:
                raise HEPpacketException
            if not payload[0] in protocol_ids:
                self.protocol = str(payload[0])
            else:
                self.protocol = protocol_ids[payload[0]]
        elif type_id >= 0x0003 and type_id <= 0x0006:
            expected_payload_len = 4 if type_id <= 0x0004 else 16
            if len(payload) != expected_payload_len:
                raise HEPpacketException
            if type_id == 0x0003 or type_id == 0x0005:
                self.src_addr = payload
            else:
                self.dst_addr = payload
        elif type_id == 0x0007 or type_id == 0x0008:
            if len(payload) != 2:
                raise HEPpacketException
            port = int.from_bytes(payload,
                        byteorder="big", signed=False)
            if type_id == 7:
                self.src_port = port
            else:
                self.dst_port = port
        elif type_id == 0x0009 or type_id == 0x000a:
            if len(payload) != 4:
                raise HEPpacketException
            timespec = int.from_bytes(payload,
                        byteorder="big", signed=False)
            if type_id == 0x0009:
                self.ts = timespec
            else:
                self.tms = timespec
        elif type_id == 0x000b:
            if len(payload) != 1:
                raise HEPpacketException
            if not payload[0] in protocol_types:
                self.type = str(payload[0])
            else:
                self.type = protocol_types[payload[0]]
        elif type_id == 0x000c:
            pass # capture id not used now
        elif type_id == 0x000f:
            self.data = payload
        elif type_id == 0x0011:
            self.correlation = payload
        else:
            logger.warning("unhandled payload type {}".format(type_id))

class trace(Module):

    def __print_hep(self, packet):
        # this works as a HEP parser
        logger.debug("initial packet size is {}".format(len(packet)))

        while len(packet) > 0:
            if len(packet) < 4:
                return packet
            # currently only HEPv3 is accepted
            if packet[0:4] != b'HEP3':
                logger.warning("packet not HEPv3: [{}]".format(packet[0:4]))
                return None
            length = int.from_bytes(packet[4:6], byteorder="big", signed=False)
            if length > len(packet):
                logger.debug("partial packet: {} out of {}".
                        format(len(packet), length))
                # wait for entire packet to parse it
                return packet
            logger.debug("packet size is {}".format(length))
            # skip the header
            hep_packet = HEPpacket(packet[6:length])
            try:
                hep_packet.parse()
            except HEPpacketException:
                return None
            packet = packet[length:]
            print(hep_packet)

        return packet

    def __complete__(self, command, text, line, begidx, endidx):
        filters = [ "caller", "callee", "ip" ]

        # remove the filters already used
        filters = [f for f in filters if line.find(f + "=") == -1]
        if not command:
            return filters

        if (not text or text == "") and line[-1] == "=":
            return [""]

        ret = [f for f in filters if (f.startswith(text) and line.find(f + "=") == -1)]
        if len(ret) == 1 :
            ret[0] = ret[0] + "="
        return ret

    def __get_methods__(self):
        return None

    def do_trace(self, params):

        filters = []

        if params is None:
            caller_f = input("Caller filter: ")
            if caller_f != "":
                filters.append(caller_f)
            callee_f = input("Callee filter: ")
            if callee_f != "":
                filters.append(callee_f)
            ip_f = input("Source IP filter: ")
            if ip_f != "":
                filters.append(ip_f)
            if len(filters) == 0:
                ans = cfg.read_param(None, "No filter specified! "\
                        "Continue without a filter?", False, True)
                if not ans:
                    return False
                filters = None
        else:
            filters = params

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if cfg.exists("trace_listen_ip"):
            trace_ip = cfg.get("trace_listen_ip")
        else:
            trace_ip = "127.0.0.1"
        if cfg.exists("trace_listen_port"):
            trace_port = cfg.get("trace_listen_port")
        else:
            trace_port = 0
        s.bind((trace_ip, int(trace_port)))
        if trace_port == 0:
            trace_port = s.getsockname()[1]
        s.listen(1)
        conn = None
        trace_name = "opensips-cli.{}".format(random.randint(0, 65536))
        trace_socket = "hep:{}:{};transport=tcp;version=3".format(
                trace_ip, trace_port)
        args = {
            'id': trace_name,
            'uri': trace_socket,
        }
        if filters:
            args['filters'] = filters

        logger.debug("filters are {}".format(filters))
        trace_started = comm.execute('trace_start', args)
        if not trace_started:
            return False

        try:
            conn, addr = s.accept()
            logger.debug("New TCP connection from {}:{}".
                    format(addr[0], addr[1]))
            remaining = b''
            while True:
                data = conn.recv(TRACE_BUFFER_SIZE)
                if not data:
                    break
                remaining = self.__print_hep(remaining + data)
                if remaining is None:
                    break
        except KeyboardInterrupt:
            comm.execute('trace_stop', {'id' : trace_name }, True)
            if conn is not None:
                conn.close()
