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
import re
import time
import threading
import bisect
import random

import json
from json.decoder import WHITESPACE

JSONRPC_RCV_HOST = '127.0.0.1'
JSONRPC_RCV_PORT = 8888

DNS_THR_EVENTS = ['dns']
SQL_THR_EVENTS = ['mysql', 'pgsql']
NOSQL_THR_EVENTS = ['Cassandra', 'cachedb_local', 'MongoDB',
                    'cachedb_memcached', 'cachedb_couchbase']
SIP_THR_EVENTS = ['msg processing']

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

        try:
            kwargs['args'] = (kwargs['events'],)
            del kwargs['events']
            self.skip_summ = kwargs['skip_summ']
            del kwargs['skip_summ']
        except:
            self.skip_summ = False

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

                        params = obj['params']

                        # only process threshold events we're interested in
                        if events is None or \
                                any(params['source'].startswith(e) for e in events):
                            if 'extra' not in params:
                                params['extra'] = "<unknown>"

                            if not self.skip_summ:
                                try:
                                    thr_summary[(params['extra'],
                                                params['source'])] += 1
                                except:
                                    thr_summary[(params['extra'],
                                                params['source'])] = 1

                            bisect.insort(thr_slowest, (-params['time'],
                                            params['extra'], params['source']))
                            thr_slowest = thr_slowest[:3]

                        string = string[end:]
                        idx = WHITESPACE.match(string, 0).end()

                conn.close()

class diagnose(Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.t = None

    def startThresholdListener(self, events, skip_summ=False):
        # subscribe and listen for "query threshold exceeded" events
        self.t = ThresholdListener(events=events, skip_summ=skip_summ)
        self.t.daemon = True
        self.t.start()

    def stopThresholdListener(self):
        if self.t:
            self.t.stop()
            self.t.join()
            self.t = None

    def restartThresholdListener(self, events, skip_summ=False):
        self.stopThresholdListener()
        self.startThresholdListener(events, skip_summ)

    def print_diag_footer(self):
        print("\n{}(press Ctrl-c to exit)".format('\t' * 5))

    def diagnose_dns(self):
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
                        q[1][0], q[0]))

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
        self.print_diag_footer()

        return True

    def diagnose_sql(self):
        return self.diagnose_db(('sql', 'SQL'), SQL_THR_EVENTS)

    def diagnose_nosql(self):
        return self.diagnose_db(('cdb', 'NoSQL (CacheDB)'), NOSQL_THR_EVENTS)

    def diagnose_db(self, dbtype, events):
        # quickly ensure opensips is running
        ans = comm.execute('get_statistics', {
                'statistics': ['{}_total_queries'.format(dbtype[0]),
                                '{}_slow_queries'.format(dbtype[0])]
                })
        if ans is None:
            return

        stats = {
            'ini_total': int(ans['{}:{}_total_queries'.format(dbtype[0], dbtype[0])]),
            'ini_slow': int(ans['{}:{}_slow_queries'.format(dbtype[0], dbtype[0])]),
            }
        stats['total'] = stats['ini_total']
        stats['slow'] = stats['ini_slow']

        self.startThresholdListener(events)

        sec = 0
        try:
            while True:
                if not self.diagnose_db_loop(sec, stats, dbtype, events):
                    break
                time.sleep(1)
                sec += 1
        except KeyboardInterrupt:
            print('^C')
        finally:
            self.stopThresholdListener()

    def diagnose_db_loop(self, sec, stats, dbtype, events):
        global thr_summary, thr_slowest

        total_stat = '{}_total_queries'.format(dbtype[0])
        slow_stat = '{}_slow_queries'.format(dbtype[0])

        os.system("clear")
        print("In the last {} seconds...".format(sec))
        if not thr_summary:
            print("    {} Queries [OK]".format(dbtype[1]))
        else:
            print("    {} Queries [WARNING]".format(dbtype[1]))
            print("        * Slowest queries:")
            for q in thr_slowest:
                print("            {}: {} ({} us)".format(q[2], q[1], -q[0]))
            print("        * Constantly slow queries")
            for q in sorted([(v, k) for k, v in thr_summary.items()], reverse=True)[:3]:
                print("            {}: {} ({} times exceeded threshold)".format(
                        q[1][1], q[1][0], q[0]))

        ans = comm.execute('get_statistics',
                    {'statistics': [total_stat, slow_stat]
            })
        if not ans:
            return False

        # was opensips restarted in the meantime? if yes, resubscribe!
        if int(ans["{}:{}".format(dbtype[0], total_stat)]) < stats['total']:
            stats['ini_total'] = int(ans["{}:{}".format(dbtype[0], total_stat)])
            stats['ini_slow'] = int(ans["{}:{}".format(dbtype[0], slow_stat)])
            thr_summary = {}
            thr_slowest = []
            sec = 1
            self.restartThresholdListener(events)

        stats['total'] = int(ans["{}:{}".format(dbtype[0], total_stat)]) - \
                            stats['ini_total']
        stats['slow'] = int(ans["{}:{}".format(dbtype[0], slow_stat)]) - \
                            stats['ini_slow']

        print("        * {} / {} queries ({}%) exceeded threshold".format(
            stats['slow'], stats['total'],
            int((stats['slow'] / stats['total']) * 100) \
                    if stats['total'] > 0 else 0))
        self.print_diag_footer()

        return True

    def diagnose_sip(self):
        # quickly ensure opensips is running
        ans = comm.execute('get_statistics', {
                'statistics': ['rcv_requests', 'rcv_replies', 'slow_messages']
                })
        if ans is None:
            return

        stats = {
            'ini_total': int(ans['core:rcv_requests']) + int(ans['core:rcv_replies']),
            'ini_slow': int(ans['core:slow_messages']),
            }
        stats['total'] = stats['ini_total']
        stats['slow'] = stats['ini_slow']

        self.startThresholdListener(SIP_THR_EVENTS, skip_summ=True)

        sec = 0
        try:
            while True:
                if not self.diagnose_sip_loop(sec, stats):
                    break
                time.sleep(1)
                sec += 1
        except KeyboardInterrupt:
            print('^C')
        finally:
            self.stopThresholdListener()

    def diagnose_sip_loop(self, sec, stats):
        global thr_slowest

        os.system("clear")
        print("In the last {} seconds...".format(sec))
        if not thr_slowest:
            print("    SIP Processing [OK]")
        else:
            print("    SIP Processing [WARNING]")
            print("        * Slowest SIP messages:")
            for q in thr_slowest:
                print("            {} ({} us)".format(desc_sip_msg(q[1]), -q[0]))

        ans = comm.execute('get_statistics', {'statistics':
                            ['rcv_requests', 'rcv_replies', 'slow_messages']})
        if not ans:
            return False

        rcv_req = int(ans["core:rcv_requests"])
        rcv_rpl = int(ans["core:rcv_replies"])
        slow_msgs = int(ans["core:slow_messages"])

        # was opensips restarted in the meantime? if yes, resubscribe!
        if rcv_req + rcv_rpl < stats['total']:
            stats['ini_total'] = rcv_req + rcv_rpl
            stats['ini_slow'] = slow_msgs
            thr_slowest = []
            sec = 1
            self.restartThresholdListener(SIP_THR_EVENTS, skip_summ=True)

        stats['total'] = rcv_req + rcv_rpl - stats['ini_total']
        stats['slow'] = slow_msgs - stats['ini_slow']

        print("        * {} / {} SIP messages ({}%) exceeded threshold".format(
            stats['slow'], stats['total'],
            int((stats['slow'] / stats['total']) * 100) \
                    if stats['total'] > 0 else 0))
        self.print_diag_footer()

        return True

    def __invoke__(self, cmd, params=None):
        logger.error(params)
        if cmd == 'dns':
            return self.diagnose_dns()
        elif cmd == 'sql':
            return self.diagnose_sql()
        elif cmd == 'nosql':
            return self.diagnose_nosql()
        elif cmd == 'sip':
            return self.diagnose_sip()

    def __complete__(self, command, text, line, begidx, endidx):
        return ['']

    def __get_methods__(self):
        return ['sip', 'dns', 'sql', 'nosql', 'brief', 'full']

def desc_sip_msg(sip_msg):
    """summarizes a SIP message into a useful one-liner"""
    try:
        if sip_msg.startswith("SIP/2.0"):
            # a SIP reply
            desc = sip_msg[7:sip_msg.find("\r\n")].strip()
        else:
            # a SIP request
            desc = sip_msg[:sip_msg.find("SIP/2.0\r\n")].strip()
    except:
        desc = ""

    try:
        callid = "Call-ID: {}".format(re.search('Call-ID:(.*)\r\n',
                                    sip_msg, re.IGNORECASE).group(1).strip())
    except:
        callid = ""

    if not desc and not callid:
        desc = "??? (unknown)"

    return "{}{}{}".format(desc, ", " if desc and callid else "", callid)
