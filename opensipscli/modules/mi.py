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

import re
import json
import shlex
from collections import OrderedDict
from opensipscli.config import cfg
from opensipscli.logger import logger
from opensipscli.module import Module
from opensipscli import comm

try:
    import yaml
    yaml_available = True
except ImportError:
    yaml_available = False

# temporary special handling for commands that require array params
# format is: command: (idx, name)
MI_ARRAY_PARAMS_COMMANDS = {
    "fs_subscribe": (1, "events"),
    "fs_unsubscribe": (1, "events"),
    "b2b_trigger_scenario": (1, "scenario_params"),
    "dlg_push_var": (2, "DID"),
    "get_statistics": (0, "statistics"),
    "list_statistics": (0, "statistics"),
    "reset_statistics": (0, "statistics"),
    "trace_start": (0, "filter"),
    "raise_event": (1, "params"),
    "dfks_set_feature": (4, "values"),
}

class mi(Module):

    def print_pretty_print(self, result):
        print(json.dumps(result, indent=4))

    def print_dictionary(self, result):
        print(str(result))

    def print_lines(self, result, indent=0):
        if type(result) in [OrderedDict, dict]:
            for k, v in result.items():
                if type(v) in [OrderedDict, list, dict]:
                    print(" " * indent + k + ":")
                    self.print_lines(v, indent + 4)
                else:
                    print(" " * indent + "{}: {}". format(k, v))
        elif type(result) == list:
            for v in result:
                self.print_lines(v, indent)
        else:
            print(" " * indent + str(result))
        pass

    def print_yaml(self, result):
        if not yaml_available:
            logger.warning("yaml not available on your platform! "
                "Please install `python-yaml` package or similar!")
        else:
            print(yaml.dump(result, default_flow_style=False).strip())

    def get_params_set(self, cmds):
        l = set()
        for p in cmds:
            m = re.match('([a-zA-Z\.\-_]+)=', p)
            # if it's not a parameter name, skip
            if m:
                l.add(m.group(1))
            else:
                return None
        return l

    def get_params_names(self, line):
        cmds = shlex.split(line)
        # cmd[0] = module, cmd[1] = command
        if len(cmds) < 2:
            return None
        return self.get_params_set(cmds[2:])

    def parse_params(self, cmd, params):

        # first, we check to see if we have only named parameters
        nparams = self.get_params_set(params)
        if nparams is not None:
            logger.debug("named parameters are used")
            new_params = {}
            for p in params:
                s = p.split("=", 1)
                value = "" if len(s) == 1 else s[1]
                # check to see if we have to split them in array or not
                if cmd in MI_ARRAY_PARAMS_COMMANDS and \
                        MI_ARRAY_PARAMS_COMMANDS[cmd][1] == s[0]:
                    new_params[s[0]] = shlex.split(value)
                else:
                    new_params[s[0]] = value
        else:
            # old style positional parameters
            logger.debug("positional parameters are used")
            # if the command is not in MI_ARRAY_PARAMS_COMMANDS, return the
            # parameters as they are
            if not cmd in MI_ARRAY_PARAMS_COMMANDS:
                return params
            # build params based on their index
            new_params = params[0:MI_ARRAY_PARAMS_COMMANDS[cmd][0]]
            if params[MI_ARRAY_PARAMS_COMMANDS[cmd][0]:]:
                new_params.append(params[MI_ARRAY_PARAMS_COMMANDS[cmd][0]:])
        return new_params

    def __invoke__(self, cmd, params=None):
        params = self.parse_params(cmd, params)
        # Mi Module works with JSON Communication
        logger.debug("running command '{}' '{}'".format(cmd, params))
        res = comm.execute(cmd, params)
        if res is None:
            return -1
        output_type = cfg.get('output_type')
        if output_type == "pretty-print":
            self.print_pretty_print(res)
        elif output_type == "dictionary":
            self.print_dictionary(res)
        elif output_type == "lines":
            self.print_lines(res)
        elif output_type == "yaml":
            self.print_yaml(res)
        elif output_type == "none":
            pass # no one interested in the reply
        else:
            logger.error("unknown output_type='{}'! Dropping output!"
                    .format(output_type))
        return 0

    def __complete__(self, command, text, line, begidx, endidx):
        # TODO: shall we cache this?
        params_arr = comm.execute('which', {'command': command})
        if len(text) == 0:
            # if last character is an equal, it's probably a value, or it will
            if line[-1] == "=":
                return ['']
            params = self.get_params_names(line)
            if params is None:
                flat_list = list([item for sublist in params_arr for item in sublist])
            else:
                # check in the line to see the parameters we've used
                flat_list = set()
                for p in params_arr:
                    sp = set(p)
                    if params.issubset(sp):
                        flat_list = flat_list.union(sp)
                flat_list = flat_list - params
        else:
            flat_list = []
            for l in params_arr:
                p = [ x for x in l if x.startswith(text) ]
                if len(p) != 0:
                    flat_list += p
        l = [ x + "=" for x in list(dict.fromkeys(flat_list)) ]
        return l if len(l) > 0 else ['']

    def __exclude__(self):
        return not comm.valid()

    def __get_methods__(self):
        return comm.execute('which')
