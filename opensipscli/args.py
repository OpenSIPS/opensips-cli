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

"""
Class that instruct the default values for arguments
"""

from opensipscli import defaults

class OpenSIPSCLIArgs:

    """
    Class that contains the default values of CLI Arguments
    """
    debug = False
    print = False
    execute = True
    command = []
    config = None
    instance = defaults.DEFAULT_SECTION
    extra_options = {}

    __fields__ = ['debug',
                  'print',
                  'execute',
                  'command',
                  'config',
                  'instance',
                  'extra_options']

    def __init__(self, **kwargs):
        for k in kwargs:
            if k in self.__fields__:
                self.__setattr__(k, kwargs[k])
            else:
                self.extra_options[k] = kwargs[k]


# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

