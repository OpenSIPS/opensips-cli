#!/usr/bin/env python3

import cmd
import sys
import os
import Modules
import readline
import comm
import atexit
import config_defaults
from config import cfg
from logger import logger
from types import FunctionType

class OpenSIPSCTLShell(cmd.Cmd, object):
    cmd_list = []
    mod_list = []
    cmd_to_mod = {}

    def __init__(self, config_file, instance, new_options):
        # __init__ of the configuration file
        cfg.parse(config_file)
        if not cfg.has_instance(instance):
            logger.warning("Unknown instance '{}'! Using default instance '{}'!".
                    format(instance, config_defaults.DEFAULT_SECTION))
        cfg.set_instance(instance)
        self.current_instance = instance
        cfg.set_custom_options(new_options)
        # __init__ of cmd.Cmd module
        cmd.Cmd.__init__(self)

        # Opening the current working instance
        self.update_instance(cfg.current_instance)

        # Clear the modules and commands list
        self.cmd_list = ['clear', 'help', 'history', 'exit', 'quit']

        # Create the modules list based on the current instance
        for mod in sys.modules.keys():
            if mod.startswith('Modules.') and mod != 'Modules.module':
                mod_name = mod.split('.')[1]
                if eval('Modules.' + mod_name.title() +
                        '.__exclude__(self)') is False:
                    new_mod = eval('Modules.' + mod_name.title() + '()')
                    self.mod_list.append(new_mod)
        # Create the command list based on the loaded modules
        for i in self.mod_list:
            list = i.__get_methods__()
            for j in list:
                self.cmd_to_mod[j] = i.__class__.__name__
            self.cmd_list += list

    def update_instance(self, instance):

        # Update the intro and prompt
        self.intro = cfg.get('prompt_intro')
        self.prompt = '(%s): ' % cfg.get('prompt_name')

        # initialize communcation handler
        self.handler = comm.initialize()

    def atexit(self):
        history_file = cfg.get('history_file')
        logger.debug("saving history in {}".format(history_file))
        readline.write_history_file(history_file)

    def preloop(self):
        history_file = cfg.get('history_file')
        if readline and os.path.exists(history_file):
            readline.read_history_file(history_file)
            logger.debug("using history file {}".format(history_file))
        readline.set_history_length(int(cfg.get('history_file_size')))
        atexit.register(self.atexit)

    def postcmd(self, stop, line):

        if self.current_instance != cfg.current_instance:
            self.update_instance(cfg.current_instance)
            # make sure we update all the history information
            self.preloop()

        return stop

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

    # Overwritten function for our customized auto-complete
    def completenames(self, text, *ignored):
        dotext = text
        return [a for a in self.get_names() if a.startswith(dotext)]

    # Overwritten function for our customized auto-complete
    def complete(self, text, state):
        if state == 0:
            origline = readline.get_line_buffer()
            line = origline.lstrip()
            stripped = len(origline) - len(line)
            begidx = readline.get_begidx() - stripped
            endidx = readline.get_endidx() - stripped
            if begidx > 0:
                # TODO: Autocomplete CMD's args
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
        cmd = str(aux[0])
        params = []
        for i in aux[1:]:
            params.append(str("\'%s\'" % i))
        if cmd in self.cmd_list:
            for mod in self.mod_list:
                if self.cmd_to_mod[cmd] in str(mod):
                    mod.__invoke__(cmd, params)
                    break
        else:
            print('%s: command not found' % cmd)

    # Print history
    def do_history(self, line):
        if not line:
            with open(cfg.get('history_file')) as hf:
                for num, line in enumerate(hf, 1):
                    print(num, line, end='')

    # Used to get info for a certain command
    def do_help(self, line):
        # TODO: Add help for commands
        print("Usage:: help cmd - returns information about \"cmd\"")

    # Clear the terminal screen
    def do_clear(self, line):
        os.system('clear')

    # Commands used to exit the shell
    def do_EOF(self, line):  # It catches Ctrl+D
        print('^D')
        return True

    def do_quit(self, line):
        return True

    def do_exit(self, line):
        return True
