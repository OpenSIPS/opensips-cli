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

import json
import yaml
from opensipscli.config import cfg
from opensipscli.logger import logger
from opensipscli.module import Module
from opensipscli import comm

class mi(Module):

    def print_pretty_print(self, result):
        print(json.dumps(result, indent=4))

    def print_dictionary(self, result):
        print(str(result))

    def print_lines(self, result, indent=0):
        if type(result) == dict:
            for k, v in result.items():
                if type(v) in [dict, list]:
                    print(" " * indent + k + ":")
                    self.print_lines(v, indent + 4)
                else:
                    print(" " * indent + "{}: {}". format(k, v))
        elif type(result) == list:
            for v in result:
                self.print_lines(v, indent)
        else:
            print(" " * indent + result)
        pass

    def print_yaml(self, result):
        print(yaml.dump(result, default_flow_style=False).strip())

    def parse_params(self, params):
        # search for any '[' and ']' pairs
        new_params = []
        new_tmp_params = None
        for param in params:
            if param[0] == '[':
                new_tmp_params = []
                param = param.strip()[1:]
                if len(param) == 0:
                    param = None
            if param is not None and param[-1] == ']':
                if new_tmp_params is not None:
                    param = param.strip()[:-1]
                    if len(param) != 0:
                        new_tmp_params.append(param)
                    param = new_tmp_params
                    new_tmp_params = None
            if param is not None:
                if new_tmp_params is None:
                    new_params.append(param)
                else:
                    new_tmp_params.append(param)
        # move remaining nodes from tmp to new params
        if new_tmp_params is not None:
            # restore the first param
            new_tmp_params[0] = '[' + new_tmp_params[0]
            new_params = new_params + new_tmp_params
        return new_params


    def __invoke__(self, cmd, params=None):
        params = self.parse_params(params)
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

    def __exclude__(self):
        return not comm.valid()

    def __get_methods__(self):
        return comm.execute('which')
