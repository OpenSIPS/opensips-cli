#!/usr/bin/env python3

import comm
import json
from config import cfg
from logger import logger
from Modules import Module

class Mi(Module):

    def print_pretty_print(self, result):
        print(json.dumps(result, indent=4))

    def print_dictionary(self, result):
        print(str(result))

    def print_lines(self, result):
        # TODO: print by line
        pass

    def __invoke__(self, cmd, params=None):
        # Mi Module works with JSON Communication
        res = comm.execute(cmd, params)
        output_type = cfg.get('output_type')
        if output_type == "pretty-print":
            self.print_pretty_print(res)
        elif output_type == "dictionary":
            self.print_dictionary(res)
        elif output_type == "lines":
            self.print_lines(res)
        elif output_type == "none":
            pass # no one interested in the reply
        else:
            logger.error("unknown output_type='{}'! Dropping output!"
                    .format(output_type))

    def __get_methods__(self):
        return comm.execute('which')
