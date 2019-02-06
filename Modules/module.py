#!/usr/bin/env python3

from types import FunctionType

# Abstract class that has to be implemented by every Modul available
class Module:

    def __exclude__(self):
        return False

    def __invoke__(self, cmd, params=None):
        exec('self.' + cmd + '(' + ','.join(params) + ')')

    # def zzz_test(self):
    #     print("OK, it works!")

    def __get_methods__(self):
        return ([x for x in dir(self)
                 if not x.startswith('__') and callable(getattr(self, x))])
