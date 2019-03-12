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

import sys
import argparse
from opensipscli import cli, defaults

parser = argparse.ArgumentParser(description='OpenSIPS CLI interactive tool',
                                 prog=sys.argv[0],
                                 usage='%(prog)s [OPTIONS]',
                                 epilog='\n')

# Argument used to print the current version
parser.add_argument('-v', '--version',
                    action='version',
                    default=None,
                    version='OpenSIPS CLI {}'.format(defaults.VERSION))
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
                    default=defaults.DEFAULT_SECTION,
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
