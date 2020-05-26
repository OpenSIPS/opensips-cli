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

VERSION = '0.1.0'

DEFAULT_SECTION = 'default'
DEFAULT_NAME = 'opensips-cli'
try:
    home_dir = os.environ["HOME"]
except:
    # default home dir to root
    home_dir = "/"

"""
Default history file is in ~/.opensips-cli.history
"""
HISTORY_FILE = os.path.join(home_dir, ".{}.history".format(DEFAULT_NAME))

"""
Try configuration files in this order:
    * ~/.opensips-cli.cfg
    * /etc/opensips-cli.cfg
    * /etc/opensips/opensips-cli.cfg
"""
CFG_PATHS = [
    os.path.join(home_dir, ".{}.cfg".format(DEFAULT_NAME)),
    "/etc/{}.cfg".format(DEFAULT_NAME),
    "/etc/opensips/{}.cfg".format(DEFAULT_NAME),
]

DEFAULT_VALUES = {
    # CLI settings
    "prompt_name": "opensips-cli",
    "prompt_intro": "Welcome to OpenSIPS Command Line Interface!",
    "prompt_emptyline_repeat_cmd": "False",
    "history_file": HISTORY_FILE,
    "history_file_size": "1000",
    "output_type": "pretty-print",
    "log_level": "INFO",

    # communication information
    "communication_type": "fifo",
    "fifo_reply_dir": "/tmp",
    "fifo_file": "/tmp/opensips_fifo",
    "url": "http://127.0.0.1:8888/mi",

    # database module
    "database_url": "mysql://opensips:opensipsrw@localhost",
    "database_name": "opensips",
    "database_schema_path": "/usr/share/opensips",

    # user module
    "plain_text_passwords": "False",
}

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
