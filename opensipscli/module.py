#!/usr/bin/env python

# Abstract class that has to be implemented by every Module available
class Module:

    def __exclude__(self):
        return False

    def __invoke__(self, cmd, params=None):
        f = getattr(self, 'do_' + cmd)
        f(params)

    def __get_methods__(self):
        return ([x[3:] for x in dir(self)
                 if x.startswith('do_') and callable(getattr(self, x))])
