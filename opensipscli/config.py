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

import os
import configparser
from opensipscli import defaults
from opensipscli.logger import logger

class OpenSIPSCLIConfig:

    current_instance = defaults.DEFAULT_SECTION
    custom_options = None

    def __init__(self):
        self.config = configparser.ConfigParser(
                    defaults=defaults.DEFAULT_VALUES,
                    default_section=defaults.DEFAULT_SECTION)
        self.dynamic_options = {}

    # Read the file given as parameter in order to parse it
    def parse(self, in_file):
        if not in_file:
            logger.info("no config file used!")
        elif os.path.isfile(in_file) and os.access(in_file, os.R_OK):
            self.config.read(in_file)
        else:
            logger.error("Either file is missing or is not readable.")

    def set_custom_options(self, options):
        self.custom_options = {}
        if options is None:
            return
        for arg in options:
            parsed = arg.split('=')
            key = parsed[0]
            val = '='.join(parsed[1:])
            self.custom_options[key] = val

    # Function to get the value from a section.value
    def get(self, key):
        if self.dynamic_options and key in self.dynamic_options:
            return self.dynamic_options[key]
        if self.custom_options and key in self.custom_options:
            return self.custom_options[key]
        elif self.current_instance not in self.config:
            return defaults.DEFAULT_VALUES[key]
        else:
            return self.config[self.current_instance][key]

    # Function to set a dynamic value
    def set(self, key, value):
        self.dynamic_options[key] = value
        logger.debug("set {}={}".format(key, value))

    def mkBool(self, val):
        return val.lower() in ['yes', '1', 'true']

    def getBool(self, key):
        return self.mkBool(self.get(key))

    # checks if a configuration exists
    def exists(self, key):
        if self.dynamic_options and key in self.dynamic_options:
            return True
        if self.custom_options and key in self.custom_options:
            return True
        elif self.current_instance not in self.config:
            return key in defaults.DEFAULT_VALUES
        else:
            return key in self.config[self.current_instance]

    def set_instance(self, instance):
        self.current_instance = instance
        self.dynamic_options = {}

    def has_instance(self, instance):
        return instance in self.config

    def get_default_instance(self):
        return defaults.DEFAULT_SECTION

    # reads a param or returns a default
    def read_param(self, param, prompt, default=None, yes_no=False,
                    isbool=False, allow_empty=False):
        if param:
            if type(param) != list:
                param = [param]
            for p in param:
                if self.exists(p):
                    return self.mkBool(self.get(p)) if isbool else self.get(p)
        val = ""
        if yes_no:
            prompt = prompt + " [y/n]"
            if default is not None:
                prompt = prompt + " (default: '{}')".format("y" if default else "n")
        elif default is not None:
            prompt = prompt + " (default: '{}')".format(default)
        prompt = prompt + ": "
        while val == "":
            try:
                val = input(prompt).strip()
            except Exception as e:
                return None
            if val == "":
                if allow_empty:
                    return ""

                if default is not None:
                    return default
            elif yes_no:
                if val.lower() in ['y', 'yes']:
                    return True
                elif val.lower() in ['n', 'no']:
                    return False
                else:
                    prompt = "Please choose 'y' or 'n': "
            else:
                return val


cfg = OpenSIPSCLIConfig()
