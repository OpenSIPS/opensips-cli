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
        if len(params) == 0:
            return
        new_instance = params[0]
        if cfg.has_instance(new_instance):
            cfg.set_instance(new_instance)
        else:
            logger.error("cannot switch to instance '{}': instance not found!".format(new_instance))
            return -1
