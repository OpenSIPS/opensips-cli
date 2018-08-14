#!/usr/bin/env python3

import configparser
import os


class OpenSIPSCTLConfig:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.ConfigMap = {}

    # Read the file given as parameter in order to parse it
    def parse(self, in_file):
        if os.path.isfile(in_file) and os.access(in_file, os.R_OK):
            self.config.read(in_file)
            self.create_map()
        else:
            print("Either file is missing or is not readable.")

    # Write the options given through -o argument
    def overwrite_map(self, new_options):
        if new_options is not None:
            for arg in new_options:
                list = arg.split('.')
                sec = list[0]
                sec = sec.upper()
                list = '.'.join(list[1:])
                list = list.split('=')
                key = list[0]
                val = '='.join(list[1:])
                self.ConfigMap[sec][key] = val

    # Function to get the value from a section.value
    def get(self, section, key):
        return self.ConfigMap[section][key]

    # Create ConfigMap[section][key] = value
    def create_map(self):
        self.ConfigMap['DEFAULT'] = {}
        for key, value in self.config.items('DEFAULT'):
            self.ConfigMap['DEFAULT'][key] = value
        for sec in self.config.sections():
            _sec = sec.upper()
            self.ConfigMap[_sec] = {}
            for key, value in self.config.items(sec):
                self.ConfigMap[_sec][key] = value


Config = OpenSIPSCTLConfig()
