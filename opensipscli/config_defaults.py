#!/usr/bin/env python

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
    "comm_type": "fifo",
    "fifo_file": "/tmp/opensips_fifo",

    # database module
    "database_name": "opensips",
    "database_user": "opensips",
    "database_password": "opensipsrw",

}

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
