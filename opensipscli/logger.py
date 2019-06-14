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

"""
logger.py - implements coloured logging for the opensips-cli project
"""

import logging

#These are the sequences need to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

def formatter_message(message, use_color = True):
    if use_color:
        message = message.replace("$RESET", RESET_SEQ).replace("$BOLD", BOLD_SEQ)
    else:
        message = message.replace("$RESET", "").replace("$BOLD", "")
    return message

# Custom logger class with multiple destinations
class ColoredLogger(logging.Logger):

    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

    FORMAT = "$BOLD%(levelname)s$RESET: %(message)s"
    COLOR_FORMAT = formatter_message(FORMAT, True)

    def __init__(self, name):
        logging.Logger.__init__(self, name)

        color_formatter = ColoredFormatter(self.COLOR_FORMAT)

        console = logging.StreamHandler()
        console.setFormatter(color_formatter)

        self.addHandler(console)
        return

    def color(self, color, message):
        return COLOR_SEQ % (30 + color) + message + RESET_SEQ

class ColoredFormatter(logging.Formatter):

    LEVELS_COLORS = {
        'WARNING': ColoredLogger.YELLOW,
        'INFO': ColoredLogger.MAGENTA,
        'DEBUG': ColoredLogger.BLUE,
        'CRITICAL': ColoredLogger.YELLOW,
        'ERROR': ColoredLogger.RED
    }

    def __init__(self, msg, use_color = True):
        logging.Formatter.__init__(self, msg)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in self.LEVELS_COLORS:
            levelname_color = COLOR_SEQ % (30 + self.LEVELS_COLORS[levelname]) + levelname + RESET_SEQ
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)


logging.setLoggerClass(ColoredLogger)
logger = logging.getLogger(__name__)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
