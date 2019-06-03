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

class Module:
    """
    An abstract class, that has to be implemented by every Module that should be handled
    """

    def __exclude__(self):
        """
        indicates whether the module should be excluded
        """
        return False

    def __invoke__(self, cmd, params=None):
        """
        used to invoke a command from the module (starting with prefix 'do_')
        """
        f = getattr(self, 'do_' + cmd)
        return f(params)

    def __get_methods__(self):
         """
         returns all the available methods of the module
         if the method returns None, the do_`module_name`
         method is called for each command
         """
         return ([x[3:] for x in dir(self)
                 if x.startswith('do_') and callable(getattr(self, x))])

    def __complete__(self, command, text, line, begidx, endidx):
        """
        returns a list with all the auto-completion values
        """
        if not command:
            return ['']
        try:
            compfunc = getattr(self, 'complete_' + command)
            l = compfunc(text, line, begidx, endidx)
            if not l:
                return ['']
        except AttributeError:
            return None
        if len(l) == 1:
            l[0] += " "
        return l
