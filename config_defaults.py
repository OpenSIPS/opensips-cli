#!/usr/bin/env python

"""
Default configuration for OpenSIPS CLI
"""

import os

DEFAULT_SECTION = 'default'

# history file should be in the home of the user
HISTORY_FILE = os.path.join(os.environ["HOME"], ".opensipscli.history")

DEFAULT_VALUES = {
    # CLI settings
    "prompt_name": "opensips-cli",
    "prompt_intro": "Welcome to OpenSIPS Command Line Interface!",
    "history_file": HISTORY_FILE,
    "history_file_size": 1000,
    "output_type": "pretty-print",
    "log_level": "WARNING", # this is the default level in python logging

    # communication information
    "comm_type": "fifo",
    "fifo_file": "/tmp/opensips_fifo",

    # database module
    "database_name": "opensips",
    "database_user": "opensips",
    "database_password": "opensipsrw",

}

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
