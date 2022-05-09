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
import subprocess
import shutil
import os

DEFAULT_PROCESS_NAME = 'opensips'

class trap(Module):

    def get_process_name(self):
        if cfg.exists("process_name"):
            return cfg.get("process_name")
        else:
            return DEFAULT_PROCESS_NAME

    def get_pids(self):
        try:
            mi_pids = comm.execute('ps')
            self.pids = [str(pid['PID']) for pid in mi_pids['Processes']]
            info = ["Process ID={} PID={} Type={}".
                format(pid['ID'], pid['PID'], pid['Type'])
                for pid in mi_pids['Processes']]
            self.process_info = "\n".join(info)
        except:
            self.pids = []

    def get_gdb_output(self, pid):
        if os.path.islink("/proc/{}/exe".format(pid)):
            # get process line of pid
            process = os.readlink("/proc/{}/exe".format(pid))
        else:
            logger.error("could not find OpenSIPS process {} running on local machine".format(pid))
            return -1
        # Check if process is opensips (can be different if CLI is running on another host)
        path, filename = os.path.split(process)
        process_name = self.get_process_name()
        if filename != process_name:
            logger.error("process ID {}/{} is not OpenSIPS process".format(pid, filename))
            return -1
        logger.debug("Dumping backtrace for {} pid {}".format(process, pid))
        cmd = ["gdb", process, pid, "-batch", "--eval-command", "bt full"]
        out = subprocess.check_output(cmd)
        if len(out) != 0:
            self.gdb_outputs[pid] = out.decode()

    def do_trap(self, params, modifiers):

        self.pids = []
        self.gdb_outputs = {}
        self.process_info = ""

        trap_file = cfg.get("trap_file")
        process_name = self.get_process_name()

        logger.info("Trapping {} in {}".format(process_name, trap_file))
        if params and len(params) > 0:
            self.pids = params
        else:
            thread = Thread(target=self.get_pids)
            thread.start()
            thread.join(timeout=1)
            if len(self.pids) == 0:
                logger.warning("could not get OpenSIPS pids through MI!")
                try:
                    ps_pids = subprocess.check_output(["pidof", process_name])
                    self.pids = ps_pids.decode().split()
                except:
                    logger.warning("could not find any OpenSIPS running!")
                    self.pids = []

        if len(self.pids) < 1:
            logger.error("could not find OpenSIPS' pids")
            return -1

        logger.debug("Dumping PIDs: {}".format(", ".join(self.pids)))

        threads = []
        for pid in self.pids:
            thread = Thread(target=self.get_gdb_output, args=(pid,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        if len(self.gdb_outputs) == 0:
            logger.error("could not get output of gdb")
            return -1

        with open(trap_file, "w") as tf:
            tf.write(self.process_info)
            for pid in self.pids:
                if pid not in self.gdb_outputs:
                    logger.warning("No output from pid {}".format(pid))
                    continue
                try:
                    procinfo = subprocess.check_output(
                        ["ps", "--no-headers", "-ww", "-fp", pid]).decode()[:-1]
                except:
                    procinfo = "UNKNOWN"

                tf.write("\n\n---start {} ({})\n{}".
                        format(pid, procinfo, self.gdb_outputs[pid]))

        print("Trap file: {}".format(trap_file))

    def __get_methods__(self):
        return None

    def __exclude__(self):
        valid = comm.valid()
        if not valid[0]:
            return False, valid[1]
        # check to see if we have gdb installed
        return (shutil.which("gdb") is None, None)
