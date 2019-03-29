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

from opensipscli.module import Module
from opensipscli.logger import logger
from opensipscli.config import cfg
from opensipscli import comm
from threading import Thread
import socket
import subprocess
import shutil
import time
import os
import time
import threading
import bisect
import random

import json
from json.decoder import WHITESPACE

JSONRPC_RCV_HOST = '127.0.0.1'
JSONRPC_RCV_PORT = 8888

thr_summary = {}
thr_slowest = []

def thresholdEventListener(subsystem=None):
    global thr_summary, thr_slowest

    thr_summary = {}
    thr_slowest = []

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((JSONRPC_RCV_HOST, JSONRPC_RCV_PORT))
        s.listen()

        comm.execute("event_subscribe", {
                'event': 'E_CORE_THRESHOLD',
                'socket': 'jsonrpc:{}:{}'.format(
                            JSONRPC_RCV_HOST, JSONRPC_RCV_PORT)
                })
        conn, addr = s.accept()
        with conn:
            string = ""
            while True:
                new = conn.recv(1024).decode('utf-8')
                if not new:
                    break

                string += new

                decoder = json.JSONDecoder()
                idx = WHITESPACE.match(string, 0).end()
                while idx < len(string):
                    obj, end = decoder.raw_decode(string, idx)

                    # only process threshold events we're interested in
                    if subsystem is None or obj['params']['source'] == subsystem:
                        try:
                            thr_summary[obj['params']['extra']] += 1
                        except:
                            thr_summary[obj['params']['extra']] = 1
                        bisect.insort(thr_slowest, (-obj['params']['time'],
                                                 obj['params']['extra']))
                        thr_slowest = thr_slowest[:3]

                    string = string[end:]
                    idx = WHITESPACE.match(string, 0).end()

def DNSThresholdEventListener():
    thresholdEventListener('dns')

class diagnose(Module):
    def startThresholdListener(self, job):
        # subscribe and listen for "query threshold exceeded" events
        self.t = threading.Thread(target=job)
        self.t.daemon = True
        self.t.start()

    def restartThresholdListener(self, job):
        self.t.join()
        self.startThresholdListener(job)

    def diagnose_dns(self):
        global thr_summary, thr_slowest

        # quickly ensure opensips is running
        ans = comm.execute('get_statistics', {
                'statistics': ['dns_total_queries', 'dns_slow_queries']
                })
        if ans is None:
            return

        ini_total = int(ans['dns:dns_total_queries'])
        ini_slow = int(ans['dns:dns_slow_queries'])
        total = ini_total
        slow = ini_slow

        self.startThresholdListener(DNSThresholdEventListener)

        sec = 0
        while True:
            os.system("clear")
            print("In the last {} seconds...".format(sec))
            if not thr_summary:
                print("    DNS Queries [OK]".format(sec))
            else:
                print("    DNS Queries [WARNING]".format(sec))
                print("        * Slowest queries:")
                for q in thr_slowest:
                    print("            {} ({} us)".format(q[1], -q[0]))
                print("        * Constantly slow queries")
                for q in sorted([(v, k) for k, v in thr_summary.items()], reverse=True)[:3]:
                    print("            {} ({} times exceeded threshold)".format(
                            q[1], q[0]))

            ans = comm.execute('get_statistics', {
                    'statistics': ['dns_total_queries', 'dns_slow_queries']
                    })

            # was opensips restarted in the meantime? if yes, resubscribe!
            if int(ans['dns:dns_total_queries']) < total:
                ini_total = int(ans['dns:dns_total_queries'])
                ini_slow = int(ans['dns:dns_slow_queries'])
                thr_summary = {}
                thr_slowest = []
                sec = 1
                self.restartThresholdListener(DNSThresholdEventListener)

            total = int(ans['dns:dns_total_queries']) - ini_total
            slow = int(ans['dns:dns_slow_queries']) - ini_slow

            print("        * {} / {} queries ({}%) exceeded threshold".format(
                    slow, total, (slow // total) * 100 if total > 0 else 0))

            time.sleep(1)
            sec += 1

    def __invoke__(self, cmd, params=None):
        if cmd == 'dns':
            return self.diagnose_dns()

    def __complete__(self, command, text, line, begidx, endidx):
        return ['']

    def __get_methods__(self):
        return ['dns', 'brief', 'full']
