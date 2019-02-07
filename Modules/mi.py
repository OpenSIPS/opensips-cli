#!/usr/bin/env python3

import comm
import json
import yaml
from config import cfg
from logger import logger
from Modules import Module

class Mi(Module):

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

    def __invoke__(self, cmd, params=None):
        # Mi Module works with JSON Communication
        res = comm.execute(cmd, params)
        if res is None:
            return
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

    def __get_methods__(self):
        return comm.execute('which')
