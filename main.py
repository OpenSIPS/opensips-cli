import argparse
from config_parser import *
from cli import *

parser = argparse.ArgumentParser(description='OpenSIPSCTL Tool',
                                 prog='opensipsctl', usage='%(prog)s[OPTIONS]',
                                 epilog='\n')

# Argument used to run the command in batch mode
parser.add_argument('-x', '--batch', action='store_true', default=False,
                    help='run the command in batch mode')
# Argument used to specify a configuration file
parser.add_argument('-f', '--config', metavar='[FILE]', type=str,
                    default='./docs/default_conf.ini',
                    help='used to specify a configuration file')
# Argument used to enable debugging
parser.add_argument('-d', '--debug', action='store_true', default=False,
                    help='enable debugging')
# Argument used to overwrite certain values in the config
parser.add_argument('-o', '--option', metavar='[SECTION.KEY=VALUE]',
                    action='append', type=str, default=None,
                    help='overwrite certain values in the config')
# Argument used to print the current version
parser.add_argument('-V', '--version', action='version', default=None,
                    version='OpenSIPS 1.0')

# Parse all arguments
args = parser.parse_args()

# print(args)
BATCH = args.batch
CONFIG_FILE = args.config
DEBUG = args.debug

# Open the ConfigParser for CONFIG_FILE
Config.parse(CONFIG_FILE)

# Overwrite the ConfigMap
if args.option is not None:
    for arg in args.option:
        list = arg.split('.')
        sec = list[0]
        sec = sec.upper()
        list = '.'.join(list[1:])
        list = list.split('=')
        key = list[0]
        val = '='.join(list[1:])
        Config.ConfigMap[sec][key] = val

# Open the CLI
Shell = OpenSIPSCTLShell()
Shell.cmdloop()
