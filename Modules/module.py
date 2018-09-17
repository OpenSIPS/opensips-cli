#!/usr/bin/env python3

from types import FunctionType


class Module:

    def __exclude__(self):
        return False

    def __invoke__(self, cmd, params=None):
        exec('self.' + cmd + '(' + ','.join(params) + ')')

    def __get_methods__(self):
        return ([x for x in dir(self)
                 if not x.startswith('__') and callable(getattr(self, x))])
