# OpenSIPS CLI (Command Line Interface)

OpenSIPS CLI is an interactive command line tool that can be used to control
and monitor **OpenSIPS SIP servers**. It uses the Management Interface
exported by OpenSIPS over JSON-RPC to gather raw information from OpenSIPS and
display it in a nicer, more structured manner to the user.

The tool is very flexible and has a modular design, consisting of multiple
modules that implement different features. New modules can be easily added by
creating a new module that implements the [OpenSIPS CLI
Module](opensipscli/module.py) Interface.

OpenSIPS CLI is an interactive console that features auto-completion and
reverse/forward command history search, but can also be used to execute
one-liners for automation purposes.

OpenSIPS CLI can communicate with an OpenSIPS server using different transport
methods, such as fifo or http.

# Compatibility

This tool uses the new JSON-RPC interface added in OpenSIPS 3.0, therefore
it can only be used with OpenSIPS versions higher than or equal to 3.0.  For older
versions of OpenSIPS, use the classic `opensipsctl` tool from the `opensips` project.

## Usage

Simply run `opensips-cli` tool directly in your cli.
By default the tool will start in interactive mode.

OpenSIPS CLI accepts the following arguments:
* `-h|--help` - used to display information about running `opensips-cli`
* `-v|--version` - displays the version of the running tool
* `-d|--debug` - starts the `opensips-cli` tool with debugging enabled
* `-f|--config` - specifies a configuration file (see [Configuration
Section](#configuration) for more information)
* `-i|--instance INSTANCE` - changes the configuration instance (see [Instance
Module](docs/modules/instance.md) Documentation for more information)
* `-o|--option KEY=VALUE` - sets/overwrites the `KEY` configuration parameter
with the specified `VALUE`. Works for both core and modules parameters. Can be
used multiple times, for different options
* `-x|--execute` - executes the command specified and exits

In order to run `opensips-cli` without installing it, you have to export the
`PYTHONPATH` variable to the root of the `opensipscli` package. If you are in
the root of the project, simply do:

```
export PYTHONPATH=.
bin/opensips-cli
```

## Configuration

OpenSIPS CLI accepts a configuration file, formatted as an `ini` or `cfg`
file, that can store certain parameters that influence the behavior of the
OpenSIPS CLI tool. You can find [here](etc/default.cfg) an example of a
configuration file that behaves exactly as the default parameters. The set of
default values used, when no configuration file is specified, can be found
[here](opensipscli/defaults.py).

The configuration file can have multiple sections/instances, managed by the
[Instance](docs/modules/instance.md) module. One can choose different
instances from the configuration file by specifying the `-i INSTANCE` argument
when starting the cli tool.

If no configuration file is specified by the `-f|--config` argument, OpenSIPS
CLI searches for one in the following locations:

* `~/.opensips-cli.cfg` (highest precedence)
* `/etc/opensips-cli.cfg`
* `/etc/opensips/opensips-cli.cfg` (lowest precedence)

If no file is found, it starts with the default configuration.

The OpenSIPS CLI core can use the following parameters:

* `prompt_name`: The name of the OpenSIPS CLI prompt (Default: `opensips-cli`)
* `prompt_intro`: Introduction message when entering the OpenSIPS CLI
* `prompt_emptyline_repeat_cmd`: Repeat the last command on an emptyline (Default: `False`)
* `history_file`: The path of the history file (Default: `~/.opensips-cli.history`)
* `history_file_size`: The backlog size of the history file (Default: `1000`)
* `log_level`: The level of the console logging (Default: `WARNING`)
* `communication_type`: Communication transport used by OpenSIPS CLI (Default: `fifo`)
* `fifo_file`: The OpenSIPS FIFO file to which the CLI will write commands
(Default: `/var/run/opensips/opensips_fifo`)
* `fifo_file_fallback`: A fallback FIFO file that is being used when the `fifo_file`
is not found - this has been introduces for backwards compatibility when the default
`fifo_file` has been changed from `/tmp/opensips_fifo` (Default: `/tmp/opensips_fifo`)
* `fifo_reply_dir`: The default directory where `opensips-cli` will create the
fifo used for the reply from OpenSIPS (Default: `/tmp`)
* `url`: The default URL used when `http` `communication_type` is used
(Default: `http://127.0.0.1:8888/mi`).

Each module can use each of the parameters above, but can also declare their
own. You can find in each module's documentation page the parameters that they
are using.

It is also possible to set a parameters dynamically, using the `set` command.
This configuration is only available during the current interactive session,
and also gets cleaned up when an instance is switched.

## Modules

The OpenSIPS CLI tool consists of the following modules:
* [Management Interface](docs/modules/mi.md) - run MI commands
* [Database](docs/modules/database.md) - commands to create, modify, drop, or
migrate an OpenSIPS database
* [Diagnose](docs/modules/diagnose.md) - instantly diagnose OpenSIPS instances
* [Instance](docs/modules/instance.md) - used to switch through different
instances/configuration within the config file
* [User](docs/modules/user.md) - utility used to add and remove OpenSIPS users
* [Trace](docs/modules/trace.md) - trace calls information from users
* [Trap](docs/modules/trap.md) - use `gdb` to take snapshots of OpenSIPS workers
* [TLS](docs/modules/tls.md) - utility to generate certificates for TLS

## Communication

OpenSIPS CLI can communicate with an OpenSIPS instance through MI using
different transports. Supported transports at the moment are:
* `FIFO` - communicate over the `mi_fifo` module
* `HTTP` - use JSONRPC over HTTP through the `mi_http` module

## Installation

Please follow the details provided in the
<a href="docs/INSTALLATION.md">Installation</a> section, for a complete guide
on how to install `opensips-cli` as a replacement for the deprecated
`opensipsctl` shell script.

## Contribute

Feel free to contribute to this project with any module, or functionality you
find useful by opening a pull request.

## History

This project was started by **Dorin Geman**
([dorin98](https://github.com/dorin98)) as part of the [ROSEdu
2018](http://soc.rosedu.org/2018/) program. It has later been adapted to the
new OpenSIPS 3.0 MI interface and became the main external tool for managing
OpenSIPS.

## License

<!-- License source -->
[License-GPLv3]: https://www.gnu.org/licenses/gpl-3.0.en.html "GNU GPLv3"
[Logo-CC_BY]: https://i.creativecommons.org/l/by/4.0/88x31.png "Creative Common Logo"
[License-CC_BY]: https://creativecommons.org/licenses/by/4.0/legalcode "Creative Common License"

The `opensips-cli` source code is licensed under the [GNU General Public License v3.0][License-GPLv3]

All documentation files (i.e. `.md` extension) are licensed under the [Creative Common License 4.0][License-CC_BY]

![Creative Common Logo][Logo-CC_BY]

© 2018 - 2020  OpenSIPS Solutions
