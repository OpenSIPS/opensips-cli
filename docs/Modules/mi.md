# OpenSIPS CLI - Management Interface module

This module can be used by the `opensips-cli` tool to execute JSON-RPC
commands and display the result in the console.

## Commands

This module exports all the commands that are exported by the OpenSIPS
instance that `opensips-cli` points to. It fetches the available commands by
running the OpenSIPS MI `which` command. When running a command, it returns
the raw, unprocessed data from OpenSIPS.

## Configuration

This module can accept the following parameters in the config file:
* `output_type`: indicates the format of the output printed. Possible values
are:
  * `pretty-print` - (default) prints the output in a pretty-prited JSON format
  * `dictionary` - prints the output as a JSON dictionary
  * `lines` - prints the output on indented lines
  * `yaml` - prints the output in a YAML format
  * `none` - does not print anything

## Examples

Fetch the OpenSIPS `uptime` in a YAML format:
```
opensips-cli -o output_type=yaml -x mi uptime
Now: Wed Feb 20 13:37:25 2019
Up since: Tue Feb 19 14:48:41 2019
```

Display the load and networking statistics one on each line:
```
opensips-cli -o output_type=lines -x mi get_statistics [load net:]
load:load: 0
net:waiting_udp: 0
net:waiting_tcp: 0
net:waiting_tls: 0
```
