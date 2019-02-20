#!/usr/bin/env python

from opensipscli.config import cfg
from opensipscli.logger import logger
from opensipscli.module import Module

class instance(Module):

    def get_instances(self):
        l = cfg.config.sections()
        default_section = cfg.get_default_instance()
        if default_section not in l:
            l.insert(0, default_section)
        return l

    def do_show(self, params):
        print(cfg.current_instance)

    def do_list(self, params):
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
            return -1
