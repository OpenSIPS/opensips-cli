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

import cmd
import sys
import os
import shlex
import readline
import atexit
import importlib
from opensipscli import comm
from opensipscli import defaults
from opensipscli.config import cfg
from opensipscli.logger import logger
from opensipscli.modules import *

class OpenSIPSCLIShell(cmd.Cmd, object):
    """
    OpenSIPS-Cli shell
    """
    modules = {}
    registered_atexit = False

    def __init__(self, options):
        """
        contructor for OpenSIPS-Cli
        """

        self.debug = options.debug
        self.execute = options.execute
        self.command = options.command
        self.modules_dir_inserted = None

        if self.debug:
            logger.setLevel("DEBUG")

        if not options.config:
            cfg_file = None
            for f in defaults.CFG_PATHS:
                if os.path.isfile(f) and os.access(f, os.R_OK):
                    # found a valid config file
                    cfg_file = f
                    break
        else:
            cfg_file = options.config
        if not cfg_file:
            logger.debug("no config file found in any of {}".
                    format(", ".join(defaults.CFG_PATHS)))
        else:
            logger.debug("using config file {}".format(cfg_file))

        # __init__ of the configuration file
        cfg.parse(cfg_file)
        if not cfg.has_instance(options.instance):
            logger.warning("Unknown instance '{}'! Using default instance '{}'!".
                    format(options.instance, defaults.DEFAULT_SECTION))
            instance = defaults.DEFAULT_SECTION
        else:
            instance = options.instance
        cfg.set_instance(instance)
        cfg.set_custom_options(options.extra_options)

        if not self.execute:
            # __init__ of cmd.Cmd module
            cmd.Cmd.__init__(self)

        # Opening the current working instance
        self.update_instance(cfg.current_instance)

    def update_logger(self):
        """
        alter logging level
        """

        # first of all, let's handle logging
        if self.debug:
            level = "DEBUG"
        else:
            level = cfg.get("log_level")
        logger.setLevel(level)

    def clear_instance(self):
        """
        update history
        """
        # make sure we dump everything before swapping files
        self.history_write()

    def update_instance(self, instance):
        """
        constructor of an OpenSIPS-Cli instance
        """

        # first of all, let's handle logging
        self.current_instance = instance
        self.update_logger()

        # Update the intro and prompt
        self.intro = cfg.get('prompt_intro')
        self.prompt = '(%s): ' % cfg.get('prompt_name')

        # initialize communcation handler
        self.handler = comm.initialize()

        # remove all loaded modules
        self.modules = {}

        if not self.execute:
            print(self.intro)
            # add the built-in modules and commands list
            for mod in ['set', 'clear', 'help', 'history', 'exit', 'quit']:
                self.modules[mod] = (self, None)

        if not cfg.exists('skip_modules'):
            skip_modules = []
        else:
            skip_modules = cfg.get('skip_modules')

        available_modules = { key[20:]: sys.modules[key] for key in
                sys.modules.keys() if
                key.startswith("opensipscli.modules.") and
                key[20:] not in skip_modules }
        for name, module in available_modules.items():
            m = importlib.import_module("opensipscli.modules.{}".format(name))
            if not hasattr(m, "Module"):
                logger.debug("Skipping module '{}' - does not extend Module".
                        format(name))
                continue
            if not hasattr(m, name):
                logger.debug("Skipping module '{}' - module implementation not found".
                        format(name))
                continue
            mod = getattr(module, name)
            if not hasattr(mod, '__exclude__') or not hasattr(mod, '__get_methods__'):
                logger.debug("Skipping module '{}' - module does not implement Module".
                        format(name))
                continue
            if mod.__exclude__(mod):
                logger.debug("Skipping module '{}' - excluded on purpose".format(name))
                continue
            logger.debug("Loaded module '{}'".format(name))
            imod = mod()
            self.modules[name] = (imod, mod.__get_methods__(imod))

    def history_write(self):
        """
        save history file
        """
        history_file = cfg.get('history_file')
        logger.debug("saving history in {}".format(history_file))
        os.makedirs(os.path.expanduser(os.path.dirname(history_file)), exist_ok=True)
        try:
            readline.write_history_file(os.path.expanduser(history_file))
        except PermissionError:
            logger.warning("failed to write CLI history to {} " +
                            "(no permission)".format(
                history_file))

    def preloop(self):
        """
        preload a history file
        """
        history_file = cfg.get('history_file')
        logger.debug("using history file {}".format(history_file))
        try:
            readline.read_history_file(os.path.expanduser(history_file))
        except PermissionError:
            logger.warning("failed to read CLI history from {} " +
                            "(no permission)".format(
                history_file))
        except FileNotFoundError:
            pass

        readline.set_history_length(int(cfg.get('history_file_size')))
        if not self.registered_atexit:
            atexit.register(self.history_write)

    def postcmd(self, stop, line):
        """
        post command after switching instance
        """
        if self.current_instance != cfg.current_instance:
            self.clear_instance()
            self.update_instance(cfg.current_instance)
            # make sure we update all the history information
            self.preloop()

        return stop

    def print_topics(self, header, cmds, cmdlen, maxcol):
        """
        print topics, omit misc commands
        """
        if header is not None:
            if cmds:
                self.stdout.write('%s\n' % str(header))
                if self.ruler:
                    self.stdout.write('%s\n' % str(self.ruler*len(header)))
                self.columnize(cmds, maxcol-1)
                self.stdout.write('\n')

    def cmdloop(self, intro=None):
        """
        command loop, catching SIGINT
        """
        if self.execute:
            if len(self.command) < 1:
                logger.error("no modules to run specified!")
                return -1
            if len(self.command) < 2:
                logger.debug("no method to in '{}' run specified!".
                        format(self.command[0]))
                command = None
                params = None
            else:
                command = self.command[1]
                params = self.command[2:]

            logger.debug("running in non-interactive mode '{}'".format(self.command))

            try:
                ret = self.run_command(self.command[0], command, params)
            except KeyboardInterrupt:
                print('^C')
                return -1

            # assume that by default it exists with success
            if ret is None:
                ret = 0
            return ret
        while True:
            try:
                super(OpenSIPSCLIShell, self).cmdloop(intro='')
                break
            except KeyboardInterrupt:
                print('^C')
        # any other commands exits with negative value
        return -1

    def emptyline(self):
        if cfg.getBool('prompt_emptyline_repeat_cmd'):
            super().emptyline()

    def complete_modules(self, text):
        """
        complete modules selection based on given text
        """
        l = [a for a in self.modules.keys() if a.startswith(text)]
        if len(l) == 1:
            l[0] = l[0] + " "
        return l

    def complete_functions(self, module, text, line, begidx, endidx):
        """
        complete function selection based on given text
        """

        # builtin commands
        params = line.split()
        if module[1] is not None and \
                (len(params) < 2 or (len(params) == 2 and line[-1] != ' ')):
            l = [a for a in module[1] if a.startswith(text)]
            if len(l) == 1:
                l[0] += " "
        else:
            try:
                compfunc = getattr(module[0], '__complete__')
                p = params[1] if len(params) > 1 else None
                l = compfunc(p, text, line, begidx, endidx)
                if not l:
                    return None
            except AttributeError:
                return ['']
            # looking for a different command
        return l

    # Overwritten function for our customized auto-complete
    def complete(self, text, state):
        """
        auto-complete selection based on given text and state parameters
        """
        if state == 0:
            origline = readline.get_line_buffer()
            line = origline.lstrip()
            stripped = len(origline) - len(line)
            begidx = readline.get_begidx() - stripped
            endidx = readline.get_endidx() - stripped
            if begidx > 0:
                mod, args, foo = self.parseline(line)
                if mod == '':
                    return self.complete_modules(text)[state]
                elif not mod in self.modules:
                    logger.error("BUG: mod '{}' not found!".format(mod))
                else:
                    module = self.modules[mod]
                    self.completion_matches = \
                        self.complete_functions(module, text, line, begidx, endidx)
            else:
                self.completion_matches = self.complete_modules(text)
        try:
            return self.completion_matches[state]
        except IndexError:
            return ['']

    # Execute commands from Modules
    def run_command(self, module, cmd, params):
        """
        run a module command with given parameters
        """
        try:
            mod = self.modules[module]
        except (AttributeError, KeyError):
            logger.error("no module '{}' loaded".format(module))
            return -1
        # if the module does not return any methods (returned None)
        # we simply call the module's name method
        if not mod[1]:
            if params is not None:
                params.insert(0, cmd)
            cmd = mod[0].__module__
            if cmd.startswith("opensipscli.modules."):
                cmd = cmd[20:]
        elif not cmd and '' not in mod[1]:
            logger.error("module '{}' expects the following commands: {}".
                   format(module, ", ".join(mod[1])))
            return -1
        elif cmd and not cmd in mod[1]:
            logger.error("no command '{}' in module '{}'".
                    format(cmd, module))
            return -1
        logger.debug("running command '{}' '{}'".format(cmd, params))
        return mod[0].__invoke__(cmd, params)

    def default(self, line):
        try:
            aux = shlex.split(line)
        except ValueError:
            """ if the line ends in a backspace, just clean it"""
            line = line[:-1]
            aux = shlex.split(line)

        module = str(aux[0])
        if len(aux) == 1:
            cmd = None
            params = None
        else:
            cmd = str(aux[1])
            params = aux[2:]
        self.run_command(module, cmd, params)

    def do_history(self, line):
        """
        print entries in history file
        """
        if not line:
            try:
                with open(os.path.expanduser(cfg.get('history_file'))) as hf:
                    for num, line in enumerate(hf, 1):
                        print(num, line, end='')
            except FileNotFoundError:
                pass

    def do_set(self, line):
        """
        handle dynamic settings (key-value pairs)
        """
        parsed = line.split('=', 1)
        if len(parsed) < 2:
            logger.error("setting value format is 'key=value'!")
            return
        key = parsed[0]
        value = parsed[1]
        cfg.set(key, value)

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
