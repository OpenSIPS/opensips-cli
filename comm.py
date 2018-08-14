#!/usr/bin/env python3

import communication
from cli import *


class OpenSIPSCTLComm:
    comm_type = ''
    comm_func = ''

    def __init__(self, section):
        comm_type = Config.get(section, 'comm_type')
        comm_type = 'json'
        if comm_type == 'json':
            comm_func = 'communication/opensipsctl_json'
        else:
            print("Unknown communication protocol!")

    def execute(self, cmd, args=None):
        print(communication.mi_json(cmd))
