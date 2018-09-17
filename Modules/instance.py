#!/usr/bin/env python3

from Modules import Module
from config_parser import Config
import communication


class Instance(Module):

    def instance_show(self):
        print(Config.current_instance)

    def instance_list(self):
        for sec in Config.config.sections():
            print(sec)

    def instance_switch(self, new_instance):
        Config.current_instance = new_instance
