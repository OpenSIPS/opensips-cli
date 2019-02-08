#!/usr/bin/env python

import os
import configparser
from opensipscli import config_defaults
from opensipscli.logger import logger

class OpenSIPSCLIConfig:

    current_instance = config_defaults.DEFAULT_SECTION
    custom_options = None

    def __init__(self):
        self.config = configparser.ConfigParser(
                    defaults=config_defaults.DEFAULT_VALUES,
                    default_section=config_defaults.DEFAULT_SECTION)

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
        if self.custom_options and key in self.custom_options:
            return self.custom_options[key]
        elif self.current_instance not in self.config:
            return config_defaults.DEFAULT_VALUES[key]
        else:
            return self.config[self.current_instance][key]

    # checks if a configuration exists
    def exists(self, key):
        if self.custom_options and key in self.custom_options:
            return True
        elif self.current_instance not in self.config:
            return key in config_defaults.DEFAULT_VALUES
        else:
            return key in self.config[self.current_instance]

    def set_instance(self, instance):
        self.current_instance = instance

    def has_instance(self, instance):
        return instance in self.config

    def get_default_instance(self):
        return config_defaults.DEFAULT_SECTION


cfg = OpenSIPSCLIConfig()
