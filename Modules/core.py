#!/usr/bin/env python3

from comm import *


# Setup connectivity function
def __connect():
    global conn
    conn = OpenSIPSCTLComm(str(__name__).upper())


def ps(args):
    __connect()
    conn.execute("ps")
    # print(args)


def test_func(args):
    __connect()
    print('test OK')
