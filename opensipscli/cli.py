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
from opensipscli import args
from opensipscli import comm
from opensipscli import defaults
from opensipscli.config import cfg
from opensipscli.logger import logger
from opensipscli.modules import *

class OpenSIPSCLI(cmd.Cmd, object):
    """
    OpenSIPS-Cli shell
    """
    modules = {}
    excluded_errs = {}
    registered_atexit = False

    def __init__(self, options = None):
        """
        contructor for OpenSIPS-Cli
        """

        if not options:
            options = args.OpenSIPSCLIArgs()

        self.debug = options.debug
        self.print = options.print
        self.execute = options.execute
        self.command = options.command
        self.modules_dir_inserted = None

        if self.debug:
            logger.setLevel("DEBUG")

        cfg_file = None
        if not options.config:
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
        if options:
            cfg.set_custom_options(options.extra_options)

        if not self.execute:
            # __init__ of cmd.Cmd module
            cmd.Cmd.__init__(self)

        # Opening the current working instance
        self.update_instance(cfg.current_instance)

        if self.print:
            logger.info(f"Config:\n" + "\n".join([f"{k}: {v}" for k, v in cfg.to_dict().items()]))

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

        skip_modules = []
        if cfg.exists('skip_modules'):
            skip_modules = cfg.get('skip_modules')
        sys_modules = {}
        if not self.execute:
            print(self.intro)
            # add the built-in modules and commands list
            for mod in ['set', 'clear', 'help', 'history', 'exit', 'quit']:
                self.modules[mod] = (self, None)
            sys_modules = sys.modules
        else:
            try:
                mod = "opensipscli.modules.{}".format(self.command[0])
                sys_modules = { mod: sys.modules[mod] }
            except:
                pass

        available_modules = { key[20:]: sys_modules[key] for key in
                sys_modules.keys() if
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
            excl_mod = mod.__exclude__(mod)
            if excl_mod[0] is True:
                if excl_mod[1]:
                    self.excluded_errs[name] = excl_mod[1]
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

            module, command, modifiers, params = self.parse_command(self.command)

            logger.debug("running in non-interactive mode {} {} {}".
                    format(module, command, params))
            try:
                ret = self.run_command(module, command, modifiers, params)
            except KeyboardInterrupt:
                print('^C')
                return -1

            # assume that by default it exists with success
            if ret is None:
                ret = 0
            return ret
        while True:
            try:
                super(OpenSIPSCLI, self).cmdloop(intro='')
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
        _, command, modifiers, params = self.parse_command(line.split())
        # get all the available modifiers of the module
        all_params = []
        if not command:
            # haven't got to a command yet, so we might have some modifiers
            try:
                modiffunc = getattr(module[0], '__get_modifiers__')
                modifiers_params = modiffunc()
            except:
                pass
            all_params = [ x for x in modifiers_params if x not in modifiers ]
            # if we are introducing a modifier, auto-complete only them
            if begidx > 1 and line[begidx-1] == '-':
                stripped_params = [ p.lstrip("-") for p in modifiers_params ]
                l = [a for a in stripped_params if a.startswith(text)]
                if len(l) == 1:
                    l[0] = l[0] + " "
                else:
                    l = [a for a in l if a not in [ m.strip("-") for m in modifiers]]
                return l

        if module[1]:
            all_params = all_params + module[1]
        if len(all_params) > 0 and (not command or
                (len(params) == 0 and line[-1] != ' ')):
            l = [a for a in all_params if a.startswith(text)]
            if len(l) == 1:
                l[0] += " "
        else:
            try:
                compfunc = getattr(module[0], '__complete__')
                l = compfunc(command, text, line, begidx, endidx)
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

    # Parse parameters
    def parse_command(self, line):

        module = line[0]
        if len(line) < 2:
            return module, None, [], []
        paramIndex = 1
        while paramIndex < len(line):
            if line[paramIndex][0] != "-":
                break
            paramIndex = paramIndex + 1
        if paramIndex == 1:
            modifiers = []
            command = line[1]
            params = line[2:]
        elif paramIndex == len(line):
            modifiers = line[1:paramIndex]
            command = None
            params = []
        else:
            modifiers = line[1:paramIndex]
            command = line[paramIndex]
            params = line[paramIndex + 1:]

        return module, command, modifiers, params

    # Execute commands from Modules
    def run_command(self, module, cmd, modifiers, params):
        """
        run a module command with given parameters
        """
        try:
            mod = self.modules[module]
        except (AttributeError, KeyError):
            if module in self.excluded_errs:
                for err_msg in self.excluded_errs[module]:
                    logger.error(err_msg)
                return -1
            else:
                logger.error("no module '{}' loaded".format(module))
                return -1
        # if the module does not return any methods (returned None)
        # we simply call the module's name method
        if not mod[1]:
            if cmd and params is not None:
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
        return mod[0].__invoke__(cmd, params, modifiers)

    def default(self, line):
        try:
            aux = shlex.split(line)
        except ValueError:
            """ if the line ends in a backspace, just clean it"""
            line = line[:-1]
            aux = shlex.split(line)

        module, cmd, modifiers, params = self.parse_command(aux)
        self.run_command(module, cmd, modifiers, params)

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

    def mi(self, cmd, params = [], silent = False):
        """helper for running MI commands"""
        return comm.execute(cmd, params, silent)
