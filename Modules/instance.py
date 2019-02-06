#!/usr/bin/env python3

from Modules import Module
from config import cfg
from logger import logger
import communication

class Instance(Module):

    def instance_show(self):
        print(cfg.current_instance)

    def instance_list(self):
        for sec in cfg.config.sections():
            print(sec)

    def instance_switch(self, new_instance):
        if cfg.has_instance(new_instance):
            cfg.set_instance(new_instance)
        else:
            logger.error("cannot switch to instance '{}': instance not found!".format(new_instance))
