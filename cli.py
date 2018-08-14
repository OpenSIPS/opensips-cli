#!/usr/bin/env python3

import cmd
from config_parser import *
import sys
import types
import Modules


class OpenSIPSCTLShell(cmd.Cmd, object):
    cmd_list = []

    def __init__(self, config_file, new_options):
        Config.parse(config_file)
        Config.overwrite_map(new_options)
        cmd.Cmd.__init__(self)
        self.prompt = '(%s): ' % Config.ConfigMap['DEFAULT']['prompt_name']
        self.intro = Config.ConfigMap['DEFAULT']['prompt_intro']
        self.undoc_header = None
        self.cmd_list = self.get_functions_list()
        self.cmd_list += ['exit', 'quit']
        # print(self.cmd_list)

    # Overwritten funtion in order not to print misc commands
    def print_topics(self, header, cmds, cmdlen, maxcol):
        if header is not None:
            if cmds:
                self.stdout.write('%s\n' % str(header))
                if self.ruler:
                        self.stdout.write('%s\n' % str(self.ruler*len(header)))
                self.columnize(cmds, maxcol-1)
                self.stdout.write('\n')

    # Overwritten function in order to catch SIGINT
    def cmdloop(self, intro=None):
        print(self.intro)
        while True:
            try:
                super(OpenSIPSCTLShell, self).cmdloop(intro='')
                break
            except KeyboardInterrupt:
                print('^C')

    # Create cmd_list with all available functions
    def get_functions_list(self):
        cmd_list = []
        for mod in sys.modules.keys():
            if 'Modules' in str(mod) and len(str(mod)) > 7:
                mod_dir = eval('dir(' + mod + ')')
                for each_cmd in mod_dir:
                    if each_cmd.startswith('__'):
                        continue
                    verify = eval('isinstance(' + mod + '.' + each_cmd +
                                  ', types.FunctionType)')
                    if verify is True:
                        cmd_list.append(each_cmd)
        return cmd_list

    # Overwritten function for our customized auto-complete
    def completenames(self, text, *ignored):
        dotext = text
        return [a for a in self.get_names() if a.startswith(dotext)]

    # Overwritten function for our customized auto-complete
    def complete(self, text, state):
        if state == 0:
            import readline
            origline = readline.get_line_buffer()
            line = origline.lstrip()
            stripped = len(origline) - len(line)
            begidx = readline.get_begidx() - stripped
            endidx = readline.get_endidx() - stripped
            if begidx > 0:
                # TODO: CMD's args
                cmd, args, foo = self.parseline(line)
                if cmd == '':
                    compfunc = self.completedefault
                else:
                    try:
                        compfunc = getattr(self, 'complete_' + cmd)
                    except AttributeError:
                        compfunc = self.completedefault
            else:
                compfunc = self.completenames
            self.completion_matches = compfunc(text, line, begidx, endidx)
        try:
            return self.completion_matches[state]
        except IndexError:
            return None

    # Overwritten function for our customized auto-complete
    def get_names(self):
        return self.cmd_list

    # Execute commands from Modules
    def default(self, line):
        aux = line.split(' ')
        cmd = aux[0]
        args = aux[1:]
        # TODO: Search for the module
        if cmd in self.cmd_list:
            exec('Modules.core.' + cmd + '(' + str(args) + ')')
        else:
            print('%s: command not found' % cmd)

    # Commands used to exit the shell
    def do_EOF(self, line):
        print('^D')
        return True

    def do_quit(self, line):
        pass
        return True

    def do_exit(self, line):
        pass
        return True
