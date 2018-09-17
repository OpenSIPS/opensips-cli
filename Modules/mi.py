#!/usr/bin/env python3

from Modules import Module
import communication


class Mi(Module):

    def __invoke__(self, cmd, params=None):
        res = communication.mi_json(cmd)
        if res is not None:
            print(res)

    def __get_methods__(self):
        data = communication.mi_json('which')
        list = []
        for i in range(0, len(data[""])):
            list.append(data[""][i]['value'])
        return list
