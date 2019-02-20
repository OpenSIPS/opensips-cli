#!/usr/bin/env python

import sys
import argparse
from opensipscli import cli, config_defaults

parser = argparse.ArgumentParser(description='OpenSIPS CLI interactive tool',
                                 prog=sys.argv[0],
                                 usage='%(prog)s [OPTIONS]',
                                 epilog='\n')

# Argument used to print the current version
parser.add_argument('-v', '--version',
                    action='version',
                    default=None,
                    version='OpenSIPS CLI 1.0')
# Argument used to enable debugging
parser.add_argument('-d', '--debug',
                    action='store_true',
                    default=False,
                    help='enable debugging')
# Argument used to specify a configuration file
parser.add_argument('-f', '--config',
                    metavar='[FILE]',
                    type=str,
                    default=None,
                    help='used to specify a configuration file')
# Argument used to switch to a different instance
parser.add_argument('-i', '--instance',
                    metavar='[INSTANCE]',
                    type=str,
                    action='store',
                    default=config_defaults.DEFAULT_SECTION,
                    help='choose an opensips instance')
# Argument used to overwrite certain values in the config
parser.add_argument('-o', '--option',
                    metavar='[KEY=VALUE]',
                    action='append',
                    type=str,
                    dest="extra_options",
                    default=None,
                    help='overwrite certain values in the config')
# Argument used to run the command in non-interactive mode
parser.add_argument('-x', '--execute',
                    action='store_true',
                    default=False,
                    help='run the command in non-interactive mode')
# Argument used to specify the command to run
parser.add_argument('command',
                    nargs='*',
                    default=[],
                    help='the command to run')

def main():

    # Parse all arguments
    args = parser.parse_args()

    # Open the CLI
    shell = cli.OpenSIPSCLIShell(args)
    sys.exit(shell.cmdloop())

if __name__ == '__main__':
    main()
