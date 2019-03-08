# OpenSIPS CLI - Management Interface module

This module can be used by the `opensips-cli` tool to execute JSON-RPC
commands and display the result in the console.

## Commands

This module exports all the commands that are exported by the OpenSIPS
instance that `opensips-cli` points to. It fetches the available commands by
running the OpenSIPS MI `which` command. When running a command, it returns
the raw, unprocessed data from OpenSIPS.

Commands using this module can be run in two manners:
* using *positional* parameters: this is similar to the old way the
`opensipsctl` tool was working: the parameters passed to the function are
specified in the same order to the MI interface, in a JSON-RPC array
* using *named* parameters: parameters should be specified using their name
**Note**: due to the new OpenSIPS MI interface, some functions (such as
`sip_trace`, `dlg_list`) can no longer be used using positional parameters,
and they have to be specified using named parameters.

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
**Note**: the `get_statistics` command receives the statistics as an array
parameter
```
opensips-cli -o output_type=lines -x mi get_statistics load net:
load:load: 0
net:waiting_udp: 0
net:waiting_tcp: 0
net:waiting_tls: 0
```

The command ran is similar to the following one, but parameters are specified
using their names:
```
opensips-cli -o output_type=lines -x mi get_statistics statistics='load net:'
load:load: 0
net:waiting_udp: 0
net:waiting_tcp: 0
net:waiting_tls: 0
```

## Limitations

Some commands in OpenSIPS (such as `get_statistics`, or `dlg_push_var`)
require array parameters. Since the current OpenSIPS MI interface does not
allow us to query which parameter is an array, this is currently statically
provisioned in the [mi](opensipscli/modules/mi.py) module, the
`MI_ARRAY_PARAMS_COMMANDS` parameter. **Note:** if a new command that requires
array arguments is defined in OpenSIPS, this array has to be updated!.
