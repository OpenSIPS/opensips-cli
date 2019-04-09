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

DNS_THR_EVENTS = ['dns']
SQL_THR_EVENTS = ['mysql query', 'mysql prep stmt', 'mysql async query',
                    'pgsql query', 'postgres async query']

thr_summary = {}
thr_slowest = []

""" cheers to Philippe: https://stackoverflow.com/a/325528/2054305 """
class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

class ThresholdListener(StoppableThread):
    def __init__(self, *args, **kwargs):
        kwargs['target'] = self.listen
        kwargs['args'] = (kwargs['events'],)
        del kwargs['events']
        super().__init__(*args, **kwargs)
        self.last_subscribe_ts = 0

    def mi_refresh_sub(self):
        now = int(time.time())
        if now <= self.last_subscribe_ts + 5:
            return

        comm.execute("event_subscribe", {
                'event': 'E_CORE_THRESHOLD',
                'socket': 'jsonrpc:{}:{}'.format(
                            JSONRPC_RCV_HOST, JSONRPC_RCV_PORT),
                'expire': 10,
                })

        self.last_subscribe_ts = now

    def mi_unsub(self):
        comm.execute("event_subscribe", {
                'event': 'E_CORE_THRESHOLD',
                'socket': 'jsonrpc:{}:{}'.format(
                            JSONRPC_RCV_HOST, JSONRPC_RCV_PORT),
                'expire': 0, # there is no "event_unsubscribe", this is good enough
                })

    def listen(self, events=None):
        global thr_summary, thr_slowest

        thr_summary = {}
        thr_slowest = []

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((JSONRPC_RCV_HOST, JSONRPC_RCV_PORT))
            s.settimeout(0.1)
            s.listen()

            while True:
                self.mi_refresh_sub()

                try:
                    conn, addr = s.accept()
                    conn.settimeout(0.1)
                    break
                except socket.timeout:
                    pass

                if threading.current_thread().stopped():
                    self.mi_unsub()
                    return

            with conn:
                string = ""
                while True:
                    self.mi_refresh_sub()

                    try:
                        new = conn.recv(1024).decode('utf-8')
                    except socket.timeout:
                        new = ""

                    if threading.current_thread().stopped():
                        self.mi_unsub()
                        break

                    if not new:
                        continue

                    string += new

                    decoder = json.JSONDecoder()
                    idx = WHITESPACE.match(string, 0).end()
                    while idx < len(string):
                        try:
                            obj, end = decoder.raw_decode(string, idx)
                        except json.decoder.JSONDecodeError:
                            # partial JSON -- just let it accumulate
                            break

                        if 'params' not in obj:
                            string = string[end:]
                            continue

                        # only process threshold events we're interested in
                        if events is None or obj['params']['source'] in events:
                            if 'extra' not in obj['params']:
                                obj['params']['extra'] = "<unknown>"

                            try:
                                thr_summary[obj['params']['extra']] += 1
                            except:
                                thr_summary[obj['params']['extra']] = 1
                            bisect.insort(thr_slowest, (-obj['params']['time'],
                                                     obj['params']['extra']))
                            thr_slowest = thr_slowest[:3]

                        string = string[end:]
                        idx = WHITESPACE.match(string, 0).end()

                conn.close()

class diagnose(Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.t = None

    def startThresholdListener(self, events):
        # subscribe and listen for "query threshold exceeded" events
        self.t = ThresholdListener(events=events)
        self.t.daemon = True
        self.t.start()

    def stopThresholdListener(self):
        if self.t:
            self.t.stop()
            self.t.join()
            self.t = None

    def restartThresholdListener(self, events):
        self.stopThresholdListener()
        self.startThresholdListener(events)

    def diagnose_dns(self):
        global thr_summary, thr_slowest

        # quickly ensure opensips is running
        ans = comm.execute('get_statistics', {
                'statistics': ['dns_total_queries', 'dns_slow_queries']
                })
        if ans is None:
            return

        stats = {
            'ini_total': int(ans['dns:dns_total_queries']),
            'ini_slow': int(ans['dns:dns_slow_queries']),
            }
        stats['total'] = stats['ini_total']
        stats['slow'] = stats['ini_slow']

        self.startThresholdListener(DNS_THR_EVENTS)

        sec = 0
        try:
            while True:
                if not self.diagnose_dns_loop(sec, stats):
                    break
                time.sleep(1)
                sec += 1
        except KeyboardInterrupt:
            print('^C')
        finally:
            self.stopThresholdListener()

    def diagnose_dns_loop(self, sec, stats):
        global thr_summary, thr_slowest

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
        if not ans:
            return False

        # was opensips restarted in the meantime? if yes, resubscribe!
        if int(ans['dns:dns_total_queries']) < stats['total']:
            stats['ini_total'] = int(ans['dns:dns_total_queries'])
            stats['ini_slow'] = int(ans['dns:dns_slow_queries'])
            thr_summary = {}
            thr_slowest = []
            sec = 1
            self.restartThresholdListener(DNS_THR_EVENTS)

        stats['total'] = int(ans['dns:dns_total_queries']) - stats['ini_total']
        stats['slow'] = int(ans['dns:dns_slow_queries']) - stats['ini_slow']

        print("        * {} / {} queries ({}%) exceeded threshold".format(
            stats['slow'], stats['total'],
            int((stats['slow'] / stats['total']) * 100) \
                    if stats['total'] > 0 else 0))

        return True

    def diagnose_sql(self):
        global thr_summary, thr_slowest

        # quickly ensure opensips is running
        ans = comm.execute('get_statistics', {
                'statistics': ['sql_total_queries', 'sql_slow_queries']
                })
        if ans is None:
            return

        stats = {
            'ini_total': int(ans['sql:sql_total_queries']),
            'ini_slow': int(ans['sql:sql_slow_queries']),
            }
        stats['total'] = stats['ini_total']
        stats['slow'] = stats['ini_slow']

        self.startThresholdListener(SQL_THR_EVENTS)

        sec = 0
        try:
            while True:
                if not self.diagnose_sql_loop(sec, stats):
                    break
                time.sleep(1)
                sec += 1
        except KeyboardInterrupt:
            print('^C')
        finally:
            self.stopThresholdListener()

    def diagnose_sql_loop(self, sec, stats):
        global thr_summary, thr_slowest

        os.system("clear")
        print("In the last {} seconds...".format(sec))
        if not thr_summary:
            print("    SQL Queries [OK]".format(sec))
        else:
            print("    SQL Queries [WARNING]".format(sec))
            print("        * Slowest queries:")
            for q in thr_slowest:
                print("            {} ({} us)".format(q[1], -q[0]))
            print("        * Constantly slow queries")
            for q in sorted([(v, k) for k, v in thr_summary.items()], reverse=True)[:3]:
                print("            {} ({} times exceeded threshold)".format(
                        q[1], q[0]))

        ans = comm.execute('get_statistics', {
                'statistics': ['sql_total_queries', 'sql_slow_queries']
                })
        if not ans:
            return False

        # was opensips restarted in the meantime? if yes, resubscribe!
        if int(ans['sql:sql_total_queries']) < stats['total']:
            stats['ini_total'] = int(ans['sql:sql_total_queries'])
            stats['ini_slow'] = int(ans['sql:sql_slow_queries'])
            thr_summary = {}
            thr_slowest = []
            sec = 1
            self.restartThresholdListener(SQL_THR_EVENTS)

        stats['total'] = int(ans['sql:sql_total_queries']) - stats['ini_total']
        stats['slow'] = int(ans['sql:sql_slow_queries']) - stats['ini_slow']

        print("        * {} / {} queries ({}%) exceeded threshold".format(
            stats['slow'], stats['total'],
            int((stats['slow'] / stats['total']) * 100) \
                    if stats['total'] > 0 else 0))

        return True

    def __invoke__(self, cmd, params=None):
        if cmd == 'dns':
            return self.diagnose_dns()
        elif cmd == 'sql':
            return self.diagnose_sql()

    def __complete__(self, command, text, line, begidx, endidx):
        return ['']

    def __get_methods__(self):
        return ['dns', 'sql', 'brief', 'full']
