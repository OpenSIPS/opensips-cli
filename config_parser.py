import configparser
import os


class OpenSIPSCTLConfig(object):
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.ConfigMap = {}

    def parse(self, in_file):
        if os.path.isfile(in_file) and os.access(in_file, os.R_OK):
            self.config.read(in_file)
            self.create_map()
        else:
            print("Either file is missing or is not readable.")

    def get(self, section, key):
        if section in self.config:
            if key in self.config[section]:
                return self.config[section][key]
        elif key is self.config['DEFAULT']:
            return self.config['DEFAULT'][key]
        return None

    def create_map(self):
        self.ConfigMap['DEFAULT'] = {}
        for key, value in Config.config.items('DEFAULT'):
            self.ConfigMap['DEFAULT'][key] = value
        for sec in Config.config.sections():
            _sec = sec.upper()
            self.ConfigMap[_sec] = {}
            for key, value in Config.config.items(sec):
                self.ConfigMap[_sec][key] = value


class OpenSIPSCTLConfigModule():
    def __init__(self, section):
        self.section = section

    def get(self, key):
        global Config
        return Config.get(self.section, key)


Config = OpenSIPSCTLConfig()
