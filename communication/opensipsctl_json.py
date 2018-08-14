#!/usr/bin/env python3

import sys
import urllib.parse
import urllib.request
import json


def mi_json(cmd='ps', args=None):
    IP = '127.0.0.1'
    PORT = '8888'
    params = [cmd]

    if args is not None:
        params = params + args

    if len(params) == 1:
        cmd = params[0]
    else:
        cmd = '%s?%s' % (params[1], urllib.parse.urlencode({'params':
                         ",".join(params[2:])}))

    cmd = urllib.request.urlopen('http://%s:%s/json/%s' % (IP, PORT, cmd))

    json_file = cmd.read().decode('utf-8')
    parsed_json_file = json.loads(json_file)
    return parsed_json_file


# print(mi_json(ps))
# def recursive_print(src, dpth=0, key=''):
#     tabs = lambda n: ' ' * n * 1
#     if isinstance(src, dict):
#         for key, value in src.items():
#             print(end='x')
#             recursive_print(value, dpth + 1, key)
#     elif isinstance(src, list):
#         for litem in src:
#             recursive_print(litem, dpth + 2)
#     else:
#         if key:
#             print(tabs(dpth) + '%s = %s' % (key, src))

# for x in parsed_json_file:
#     for y in parsed_json_file[x]:
#         print_dict(y)
# recursive_print(parsed_json_file)

# def id_generator(dict_var):
#       for k, v in dict_var.items():
#             if k == "Process":
#                  yield v
#             elif isinstance(v, dict):
#                  for id_val in id_generator(v):
#                        yield id_val
#
# for _ in id_generator(parsed_json_file):
#     print(_)
