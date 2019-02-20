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
Default configuration for OpenSIPS CLI
"""

import os

DEFAULT_SECTION = 'default'
DEFAULT_NAME = 'opensips-cli'

"""
Default history file is in ~/.opensips-cli.history
"""
HISTORY_FILE = os.path.join(os.environ["HOME"],
        ".{}.history".format(DEFAULT_NAME))

"""
Try configuration files in this order:
    * ~/.opensips-cli.cfg
    * /etc/opensips-cli.cfg
    * /etc/opensips/opensips-cli.cfg
"""
CFG_PATHS = [
    os.path.join(os.environ["HOME"], ".{}.cfg".format(DEFAULT_NAME)),
    "/etc/{}.cfg".format(DEFAULT_NAME),
    "/etc/opensips/{}.cfg".format(DEFAULT_NAME),
]

DEFAULT_VALUES = {
    # CLI settings
    "prompt_name": "opensips-cli",
    "prompt_intro": "Welcome to OpenSIPS Command Line Interface!",
    "history_file": HISTORY_FILE,
    "history_file_size": 1000,
    "output_type": "pretty-print",
    "log_level": "WARNING", # this is the default level in python logging
    "modules_dir": "opensipscli/modules",

    # communication information
    "communication_type": "fifo",
    "fifo_file": "/tmp/opensips_fifo",

    # database module
    "database_name": "opensips",
    "database_user": "opensips",
    "database_password": "opensipsrw",

}

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
