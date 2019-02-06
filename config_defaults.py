#!/usr/bin/env python

"""
Default configuration for OpenSIPS CLI
"""

DEFAULT_SECTION = 'default'

DEFAULT_VALUES = {
    # CLI settings
    "prompt_name": "opensipsctl",
    "prompt_intro": "Welcome to OpenSIPS Command Line Interface!",
    "history_file": "~/.opensips-cli.history",
    "history_file_size": 1000,

    # communication information
    "comm_type": "fifo",
    "fifo_file": "/tmp/opensips_fifo",

    # database module
    "database_name": "opensips",
    "database_user": "opensips",
    "database_password": "opensipsrw",

}

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
