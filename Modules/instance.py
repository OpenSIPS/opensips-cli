#!/usr/bin/env python3

from config import cfg
from logger import logger
from module import Module
import communication

class instance(Module):

    def get_instances(self):
        l = cfg.config.sections()
        if len(l) == 0:
            return [ cfg.get_default_instance() ]
        return l

    def do_show(self):
        print(cfg.current_instance)

    def do_list(self):
        for i in self.get_instances():
            print(i)

    def complete_switch(self, text, line, *ignore):
        if len(line.split(' ')) > 3:
            return []
        return [ a for a in self.get_instances() if a.startswith(text)]

    def do_switch(self, params):
        new_instance = params[0]
        if cfg.has_instance(new_instance):
            cfg.set_instance(new_instance)
        else:
            logger.error("cannot switch to instance '{}': instance not found!".format(new_instance))
