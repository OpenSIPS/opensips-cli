from logger_colors import *


class OpenSIPSLogger(object):
    # TODO: Verbose & Color On/Off
    def __init__(self, verbose=False, color=True):
        self.verbose = verbose
        self.color = color

    def debug(self, text):
        print(LoggerColors.DEBUG + "Debug: " + text + LoggerColors.ENDC)

    def waning(self, text):
        print(LoggerColors.WARNING + "Warning: " + text + LoggerColors.ENDC)

    def error(self, text):
        print(LoggerColors.ERROR + LoggerColors.BOLD + "Error: "
              + text + LoggerColors.ENDC)


''' TEST
a = OpenSIPSLogger()
a.debug("salut")
a.waning("salut")
a.error("salut") '''
