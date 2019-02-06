#!/usr/bin/env python3

from Modules import Module
from config import cfg
import communication

class Instance(Module):

    def instance_show(self):
        print(cfg.current_instance)

    def instance_list(self):
        for sec in cfg.config.sections():
            print(sec)

    def instance_switch(self, new_instance):
        cfg.current_instance = new_instance
