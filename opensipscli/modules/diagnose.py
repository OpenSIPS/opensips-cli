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

try:
    import psutil
    have_psutil = True
except:
    have_psutil = False

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

class ThresholdCollector(StoppableThread):
    def __init__(self, *args, **kwargs):
        kwargs['target'] = self.collect_events

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

        ans = comm.execute("event_subscribe", {
                'event': 'E_CORE_THRESHOLD',
                'socket': 'jsonrpc:{}:{}'.format(
                            JSONRPC_RCV_HOST, JSONRPC_RCV_PORT),
                'expire': 10,
                }, silent=True)

        self.last_subscribe_ts = now if ans == "OK" else 0

    def mi_unsub(self):
        comm.execute("event_subscribe", {
                'event': 'E_CORE_THRESHOLD',
                'socket': 'jsonrpc:{}:{}'.format(
                            JSONRPC_RCV_HOST, JSONRPC_RCV_PORT),
                'expire': 0, # there is no "event_unsubscribe", this is good enough
                }, silent=True)

    def collect_events(self, events=None):
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
                self.collect_loop(conn, events)

    def collect_loop(self, conn, events):
        global thr_summary, thr_slowest

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

class diagnose(Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.t = None

    def startThresholdCollector(self, events, skip_summ=False):
        # subscribe for, then collect "query threshold exceeded" events
        self.t = ThresholdCollector(events=events, skip_summ=skip_summ)
        self.t.daemon = True
        self.t.start()
        for i in range(15):
            if self.t.last_subscribe_ts != 0:
                return True
            time.sleep(0.05)

        logger.error("Failed to subscribe for JSON-RPC events")
        logger.error("Is the event_jsonrpc.so OpenSIPS module loaded?")
        self.stopThresholdCollector()

        return False

    def stopThresholdCollector(self):
        if self.t:
            self.t.stop()
            self.t.join()
            self.t = None

    def restartThresholdCollector(self, events, skip_summ=False):
        self.stopThresholdCollector()
        return self.startThresholdCollector(events, skip_summ)

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

        if not self.startThresholdCollector(DNS_THR_EVENTS):
            return

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
            self.stopThresholdCollector()

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
            if not self.restartThresholdCollector(DNS_THR_EVENTS):
                return

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

        if not self.startThresholdCollector(events):
            return

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
            self.stopThresholdCollector()

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
            if not self.restartThresholdCollector(events):
                return

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

        if not self.startThresholdCollector(SIP_THR_EVENTS, skip_summ=True):
            return

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
            self.stopThresholdCollector()

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
            if not self.restartThresholdCollector(SIP_THR_EVENTS, skip_summ=True):
                return

        stats['total'] = rcv_req + rcv_rpl - stats['ini_total']
        stats['slow'] = slow_msgs - stats['ini_slow']

        print("        * {} / {} SIP messages ({}%) exceeded threshold".format(
            stats['slow'], stats['total'],
            int((stats['slow'] / stats['total']) * 100) \
                    if stats['total'] > 0 else 0))
        self.print_diag_footer()

        return True

    def diagnose_mem(self):
        try:
            while True:
                if not self.diagnose_mem_loop():
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print('^C')

    def diagnose_mem_loop(self):
        os.system("clear")
        ans = comm.execute('get_statistics', {
                                'statistics': ['shmem:', 'pkmem:']})
        ps = comm.execute('ps')
        if ans is None or ps is None:
            return False

        try:
            self.diagnose_shm_stats(ans)
            print()
            self.diagnose_pkg_stats(ans, ps)
        except:
            return False

        self.print_diag_footer()
        return True

    def diagnose_shm_stats(self, stats):
        shm_total = int(stats['shmem:total_size'])
        shm_used = int(stats['shmem:real_used_size'])
        shm_max_used = int(stats['shmem:max_used_size'])

        usage_perc = int(shm_used / shm_total * 100)
        max_usage_perc = int(shm_max_used / shm_total * 100)

        if usage_perc <= 70 and max_usage_perc <= 80:
            shm_status = "OK"
        elif usage_perc <= 85 and max_usage_perc <= 90:
            shm_status = "WARNING"
        else:
            shm_status = "CRITICAL"

        print("Shared Memory Status")
        print("--------------------")
        print("    Current Usage: {} / {} ({}%)".format(human_size(shm_used),
                    human_size(shm_total), usage_perc))
        print("    Peak Usage: {} / {} ({}%)".format(human_size(shm_max_used),
                    human_size(shm_total), max_usage_perc))
        print()

        if shm_status == "OK":
            print("    {}: no issues detected.".format(shm_status))
        elif shm_status == "WARNING":
            print("""    {}: {} shared memory usage > {}%, please
             increase the "-m" command line parameter!""".format(shm_status,
                            "Current" if usage_perc > 70 else "Peak",
                            70 if usage_perc > 70 else 80))
        else:
            print("""    {}: {} shared memory usage > {}%, increase
              the "-m" command line parameter as soon as possible!!""".format(
                            shm_status, "Current" if usage_perc > 85 else "Peak",
                            85 if usage_perc > 85 else 90))

    def diagnose_pkg_stats(self, stats, ps):
        print("Private Memory Status")
        print("---------------------")

        pk_total = None
        for pno in range(1, len(ps['Processes'])):
            try:
                st_used = "pkmem:{}-real_used_size".format(pno)
                st_free = "pkmem:{}-free_size".format(pno)
                st_max_used = "pkmem:{}-max_used_size".format(pno)
            except:
                continue

            if any(s not in stats for s in [st_used, st_free, st_max_used]):
                continue

            pk_total = int(stats[st_used]) + int(stats[st_free])
            if pk_total == 0:
                continue
            break

        if not pk_total:
            return

        print("Each process has {} of private (packaged) memory.\n".format(
                human_size(pk_total)))

        issues_found = False

        for proc in ps['Processes']:
            st_used = "pkmem:{}-real_used_size".format(proc['ID'])
            st_free = "pkmem:{}-free_size".format(proc['ID'])
            st_max_used = "pkmem:{}-max_used_size".format(proc['ID'])
            if any(s not in stats for s in [st_used, st_free, st_max_used]):
                continue

            pk_used = int(stats[st_used])
            pk_total = pk_used + int(stats[st_free])
            pk_max_used = int(stats[st_max_used])
            if pk_total == 0:
                print("    Process {:>2}: no pkg memory stats found ({})".format(
                        proc['ID'], proc['Type']))
                continue

            usage_perc = int(pk_used / pk_total * 100)
            max_usage_perc = int(pk_max_used / pk_total * 100)

            if usage_perc <= 70 and max_usage_perc <= 80:
                pk_status = "OK"
            elif usage_perc <= 85 and max_usage_perc <= 90:
                pk_status = "WARNING"
                issues_found = True
            else:
                pk_status = "CRITICAL"
                issues_found = True

            print("    Process {:>2}: {:>2}% usage, {:>2}% peak usage ({})".format(
                    proc['ID'], usage_perc, max_usage_perc, proc['Type']))

            if pk_status == "WARNING":
                print("""        {}: {} private memory usage > {}%, please
                 increase the "-M" command line parameter!""".format(pk_status,
                                "Current" if usage_perc > 70 else "Peak",
                                70 if usage_perc > 70 else 80))
            elif pk_status == "CRITICAL":
                print("""        {}: {} private memory usage > {}%, increase
                  the "-M" command line parameter as soon as possible!!""".format(
                                pk_status, "Current" if usage_perc > 85 else "Peak",
                                85 if usage_perc > 85 else 90))

        if not issues_found:
            print("\n    OK: no issues detected.")

    def diagnose_load(self, transports):
        """first, we group processes by scope/interface!"""
        pgroups = self.get_opensips_pgroups()
        if pgroups is None:
            return False
        ppgroups = [pgroups]

        try:
            while True:
                if not self.diagnose_load_loop(ppgroups, transports):
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print('^C')

    def diagnose_load_loop(self, ppgroups, transports):
        pgroups = ppgroups[0]
        os.system("clear")

        print("{}OpenSIPS Processing Status".format(25 * " "))
        print()

        load = comm.execute('get_statistics', {
                                'statistics': ['load:', 'timestamp']})
        if not load:
            return False

        # if opensips restarted in the meantime -> refresh the proc groups
        if 'ts' in pgroups and int(load['core:timestamp']) < pgroups['ts']:
            pgroups = self.get_opensips_pgroups()
            pgroups['ts'] = int(load['core:timestamp'])
            ppgroups[0] = pgroups
        else:
            pgroups['ts'] = int(load['core:timestamp'])

        # fetch the network waiting queues
        if 'udp' in transports and pgroups['udp']:
            with open('/proc/net/udp') as f:
                udp_wait = [line.split() for line in f.readlines()[1:]]
            self.diagnose_transport_load('udp', pgroups, load, udp_wait)

        if 'tcp' in transports and pgroups['tcp']:
            self.diagnose_transport_load('tcp', pgroups, load, None)

        if 'hep' in transports and pgroups['hep']:
            with open('/proc/net/udp') as f:
                udp_wait = [line.split() for line in f.readlines()[1:]]
            self.diagnose_transport_load('hep', pgroups, load, udp_wait)

        print()
        print("Info: the load percentages represent the amount of time spent by an")
        print("      OpenSIPS worker processing SIP messages, as opposed to waiting")
        print("      for new ones.  The three numbers represent the 'busy' percentage")
        print("      over the last 1 sec, last 1 min and last 10 min, respectively.")
        self.print_diag_footer()

        return True

    def diagnose_transport_load(self, transport, pgroups, load, net_wait):
        for i, (iface, procs) in enumerate(pgroups[transport].items()):
            # TODO: add SCTP support
            if iface != 'TCP' and not iface.startswith('{}'.format(transport)):
                continue

            recvq = None

            if iface == 'TCP':
                print("TCP Processing")
            else:
                print("{} UDP Interface #{} ({})".format(
                        'HEP' if transport == 'hep' else 'SIP',
                        i + 1, iface))
                if iface.startswith("hep_"):
                    iface = iface[4:]

                try:
                    # 127.0.0.1:5060 -> 0100007F, 13C4
                    ip = "{:02X}{:02X}{:02X}{:02X}".format(*reversed(list(
                                map(int, iface[4:].split(':')[0].split('.')))))
                    port = hex(int(iface[4:].split(':')[1]))[2:].upper()
                    for line in net_wait:
                        if line[1] == "{}:{}".format(ip, port):
                            recvq = int("0x" + line[4].split(':')[1], 0)
                            break
                except:
                    pass

                print("    Receive Queue: {}".format(
                        "???" if recvq is None else human_size(recvq)))

            tot_cpu = 0.0
            tot_l1 = 0
            tot_l2 = 0
            tot_l3 = 0
            proc_lines = []
            for proc in procs:
                try:
                    l1 = int(load['load:load-proc-{}'.format(proc['ID'])])
                    tot_l1 += l1
                except:
                    l1 = "??"

                try:
                    l2 = int(load['load:load1m-proc-{}'.format(proc['ID'])])
                    tot_l2 += l2
                except:
                    l2 = "??"

                try:
                    l3 = int(load['load:load10m-proc-{}'.format(proc['ID'])])
                    tot_l3 += l3
                except:
                    l3 = "??"

                proc_lines.append(
                    "    Process {:>2} load: {:>2}%, {:>2}%, {:>2}% ({})".format(
                    proc['ID'], l1, l2, l3, proc['Type']))

                if have_psutil:
                    try:
                        tot_cpu += proc['cpumon'].cpu_percent(interval=None)
                    except psutil._exceptions.NoSuchProcess:
                        """opensips may be restarted in the meantime!"""

            avg_cpu = round(tot_cpu / len(procs))
            print("    Avg. CPU usage: {}% (last 1 sec)".format(avg_cpu))
            print()

            for proc_line in proc_lines:
                print(proc_line)
            print()

            if recvq:
                print("    WARNING: the receive queue is NOT empty, SIP signaling may be slower!")

            tot_l1 = round(tot_l1 / len(procs))
            tot_l2 = round(tot_l2 / len(procs))
            tot_l3 = round(tot_l3 / len(procs))

            severity = "WARNING"

            if tot_l1 > 50:
                if tot_l1 > 80:
                    severity = "CRITICAL"
                print("    {}: {}% avg. currently used worker capacity!!".format(
                            severity, tot_l1))
            elif tot_l2 > 50:
                if tot_l2 > 80:
                    severity = "CRITICAL"
                print("    {}: {}% avg. used worker capacity over the last 1 minute!".format(
                            severity, tot_l2))
            elif tot_l3 > 50:
                if tot_l3 > 80:
                    severity = "CRITICAL"
                print("    {}: {}% avg. used worker capacity over the last 10 minutes!".format(
                            severity, tot_l3))
            else:
                if not recvq:
                    print("    OK: no issues detected.")
                print("-" * 70)
                continue

            if not have_psutil:
                print("""\n    Suggestion: see the DNS/SQL/NoSQL diagnosis for any slow query
                reports, otherwise increase 'use_workers' or '{}_workers'!""".format(
                    "tcp" if transport == "tcp" else "udp"))
                print("-" * 70)
                continue

            if avg_cpu > 25:
                if avg_cpu > 50:
                    severity = "CRITICAL"
                else:
                    severity = "WARNING"
                print("    {}: CPU intensive workload detected!".format(severity))
                print("""\n    Suggestion: increase the 'use_workers' or '{}_workers'
                OpenSIPS settings or add more servers!""".format(
                        "tcp" if transport == "tcp" else "udp"))
            else:
                print("    {}: I/O intensive (blocking) workload detected!".format(severity))
                print("""\n    Suggestion: see the DNS/SQL/NoSQL diagnosis for any slow query
                reports, otherwise increase 'use_workers' or '{}_workers'!""".format(
                        "tcp" if transport == "tcp" else "udp"))

            print("-" * 70)

    def get_opensips_pgroups(self):
        ps = comm.execute('ps')
        if ps is None:
            return None

        pgroups = {
            'udp': {},
            'tcp': {},
            'hep': {},
            }
        for proc in ps['Processes']:
            if have_psutil:
                proc['cpumon'] = psutil.Process(proc['PID'])
                proc['cpumon'].cpu_percent(interval=None) # begin cyle count

            if proc['Type'].startswith("TCP "):
                """ OpenSIPS TCP is simplified, but normalize the format"""
                try:
                    pgroups['tcp']['TCP'].append(proc)
                except:
                    pgroups['tcp']['TCP'] = [proc]
            elif "hep_" in proc['Type']:
                if proc['Type'].startswith("SIP"):
                    proc['Type'] = "HEP" + proc['Type'][3:]

                try:
                    pgroups['hep'][proc['Type'][13:]].append(proc)
                except:
                    pgroups['hep'][proc['Type'][13:]] = [proc]
            elif proc['Type'].startswith("SIP receiver "):
                try:
                    pgroups['udp'][proc['Type'][13:]].append(proc)
                except:
                    pgroups['udp'][proc['Type'][13:]] = [proc]

        return pgroups

    def diagnosis_summary(self):
        try:
            while True:
                if not self.diagnosis_summary_loop():
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print('^C')

    def diagnosis_summary_loop(self):
        stats = comm.execute('get_statistics', {
            'statistics': [
                'load', 'load1m', 'load10m', 'total_size', 'real_used_size',
                'max_used_size',  'rcv_requests', 'rcv_replies', 'processes_number',
                'slow_messages', 'pkmem:', 'dns:', 'sql:', 'cdb:'
                ]})
        if not stats:
            return False

        os.system("clear")
        print("{}OpenSIPS Overview".format(" " * 25))
        print("{}-----------------".format(" " * 25))

        if 'load:load' in stats:
            l1 = int(stats['load:load'])
            l2 = int(stats['load:load1m'])
            l3 = int(stats['load:load10m'])
            if l1 > 20 or l2 > 20 or l3 > 20:
                if l1 > 40 or l2 > 40 or l3 > 40:
                    if l1 > 66 or l2 > 66 or l3 > 66:
                        severity = "CRITICAL"
                    else:
                        severity = "WARNING"
                else:
                    severity = "NOTICE"
            else:
                severity = "OK"

            print("Worker Capacity: {}{}".format(severity, "" if severity == "OK" else \
                " (run 'diagnose load' for more info)"))

        if 'shmem:total_size' in stats:
            used = int(stats['shmem:real_used_size'])
            max_used = int(stats['shmem:max_used_size'])
            total = int(stats['shmem:total_size'])

            used_perc = round(used / total * 100)
            max_used_perc = round(max_used / total * 100)
            if used_perc > 70 or max_used_perc > 80:
                if used_perc > 85 or max_used_perc > 90:
                    severity = "CRITICAL"
                else:
                    severity = "WARNING"
            else:
                severity = "OK"

            print("{:<16} {}{}".format("Shared Memory:", severity,
                "" if severity == "OK" else \
                " (run 'diagnose memory' for more info)"))

        if 'load:processes_number' in stats:
            procs = int(stats['load:processes_number'])

            severity = "OK"

            for proc in range(1, procs):
                try:
                    used = int(stats['pkmem:{}-real_used_size'.format(proc)])
                    total = used + int(stats['pkmem:{}-free_size'.format(proc)])
                    max_used = int(stats['pkmem:{}-max_used_size'.format(proc)])
                except:
                    continue

                if total == 0:
                    continue

                used_perc = round(used / total * 100)
                max_used_perc = round(max_used / total * 100)

                if used_perc > 70 or max_used_perc > 80:
                    if used_perc > 85 or max_used_perc > 90:
                        severity = "CRITICAL"
                        break
                    else:
                        severity = "WARNING"

            print("{:<16} {}{}".format("Private Memory:", severity,
                "" if severity == "OK" else \
                " (run 'diagnose memory' for more info)"))

        if 'core:slow_messages' in stats:
            slow = int(stats['core:slow_messages'])
            total = int(stats['core:rcv_requests']) + int(stats['core:rcv_replies'])

            try:
                slow_perc = round(slow / total * 100)
            except:
                slow_perc = 0

            if 0 <= slow_perc <= 1:
                severity = "OK"
            elif 2 <= slow_perc <= 5:
                severity = "NOTICE"
            elif 6 <= slow_perc <= 50:
                severity = "WARNING"
            else:
                severity = "CRITICAL"

            print("{:<16} {}{}".format("SIP Processing:", severity,
                "" if severity == "OK" else \
                " (run 'diagnose sip' for more info)"))

        if 'dns:dns_slow_queries' in stats:
            slow = int(stats['dns:dns_slow_queries'])
            total = int(stats['dns:dns_total_queries'])

            try:
                slow_perc = round(slow / total * 100)
            except:
                slow_perc = 0

            if 0 <= slow_perc <= 1:
                severity = "OK"
            elif 2 <= slow_perc <= 5:
                severity = "NOTICE"
            elif 6 <= slow_perc <= 50:
                severity = "WARNING"
            else:
                severity = "CRITICAL"

            print("{:<16} {}{}".format("DNS Queries:", severity,
                "" if severity == "OK" else \
                " (run 'diagnose dns' for more info)"))

        if 'sql:sql_slow_queries' in stats:
            slow = int(stats['sql:sql_slow_queries'])
            total = int(stats['sql:sql_total_queries'])

            try:
                slow_perc = round(slow / total * 100)
            except:
                slow_perc = 0

            if 0 <= slow_perc <= 1:
                severity = "OK"
            elif 2 <= slow_perc <= 5:
                severity = "NOTICE"
            elif 6 <= slow_perc <= 50:
                severity = "WARNING"
            else:
                severity = "CRITICAL"

            print("{:<16} {}{}".format("SQL queries:", severity,
                "" if severity == "OK" else \
                " (run 'diagnose sql' for more info)"))

        if 'cdb:cdb_slow_queries' in stats:
            slow = int(stats['cdb:cdb_slow_queries'])
            total = int(stats['cdb:cdb_total_queries'])

            try:
                slow_perc = round(slow / total * 100)
            except:
                slow_perc = 0

            if 0 <= slow_perc <= 1:
                severity = "OK"
            elif 2 <= slow_perc <= 5:
                severity = "NOTICE"
            elif 6 <= slow_perc <= 50:
                severity = "WARNING"
            else:
                severity = "CRITICAL"

            print("{:<16} {}{}".format("NoSQL Queries:", severity,
                "" if severity == "OK" else \
                " (run 'diagnose nosql' for more info)"))

        self.print_diag_footer()
        return True

    def __invoke__(self, cmd, params=None):
        if cmd is None:
            return self.diagnosis_summary()
        if cmd == 'dns':
            return self.diagnose_dns()
        if cmd == 'sql':
            return self.diagnose_sql()
        if cmd == 'nosql':
            return self.diagnose_nosql()
        if cmd == 'sip':
            return self.diagnose_sip()
        if cmd == 'memory':
            return self.diagnose_mem()
        if cmd == 'load':
            if not params:
                params = ['udp', 'tcp', 'hep']
            return self.diagnose_load(params)

    def __complete__(self, command, text, line, begidx, endidx):
        if command != 'load':
            return ['']

        transports = ['udp', 'tcp', 'hep']
        if not text:
            return transports

        ret = [t for t in transports if t.startswith(text)]
        return ret if ret else ['']

    def __get_methods__(self):
        return ['', 'sip', 'dns', 'sql', 'nosql', 'memory', 'load', 'brief', 'full']

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
        if not sip_msg or not isinstance(sip_msg, str):
            desc = "??? (unknown)"
        else:
            desc = sip_msg[:20]

    return "{}{}{}".format(desc, ", " if desc and callid else "", callid)

def human_size(bytes, units=[' bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB']):
    """ Returns a human readable string reprentation of bytes"""
    return "{:.1f}".format(bytes) + units[0] \
            if bytes < 1024 else human_size(bytes / 1024, units[1:])
