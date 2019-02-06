#!/usr/bin/env python3

import argparse
from cli import *
import config_defaults

parser = argparse.ArgumentParser(description='OpenSIPSCTL Tool',
                                 prog='opensipsctl',
                                 usage='%(prog)s [OPTIONS]',
                                 epilog='\n')

# Argument used to run the command in batch mode
parser.add_argument('-x', '--batch',
                    default=None,
                    metavar='[COMMAND]',
                    help='run the command in batch mode')
# Argument used to specify a configuration file
parser.add_argument('-f', '--config',
                    metavar='[FILE]',
                    type=str,
                    default=None,
                    help='used to specify a configuration file')
# Argument used to enable debugging
parser.add_argument('-d', '--debug',
                    action='store_true',
                    default=False,
                    help='enable debugging')
# Argument used to overwrite certain values in the config
parser.add_argument('-o', '--option',
                    metavar='[KEY=VALUE]',
                    action='append',
                    type=str,
                    dest="extra_options",
                    default=None,
                    help='overwrite certain values in the config')
parser.add_argument('-i', '--instance',
                    metavar='[INSTANCE]',
                    type=str,
                    action='store',
                    default=config_defaults.DEFAULT_SECTION,
                    help='choose an opensips instance')
# Argument used to print the current version
parser.add_argument('-V', '--version',
                    action='version',
                    default=None,
                    version='OpenSIPS CLI 1.0')

# Parse all arguments
args = parser.parse_args()

# Open the CLI
Shell = OpenSIPSCTLShell(args)
Shell.cmdloop()
