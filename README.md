# OpenSIPS CLI (Command Line Interface)

OpenSIPS CLI is an interactive command line tool that can be used to control
and monitor **OpenSIPS SIP servers**. It uses the Management Interface
exported by OpenSIPS over JSON-RPC to gather raw information from OpenSIPS and
display it in a nicer, more structured manner to the user.

The tool is very flexible and has a modular design, consisting of multiple
modules that implement different features. New modules can be easily added by
creating a new module that implements the [OpenSIPS CLI
Module](opensipscli/module.py) Interface.

OpenSIPS CLI is an interactive console that features auto-completion, commands
history and navigation, but can also be used to execute one-liners.

OpenSIPS CLI can communicate with an OpenSIPS server using different transport
methods, such as fifo or http.

# Compatibility

This tool uses the new JSON-RPC Interface in OpenSIPS, that has been added in
OpenSIPS 3.0. Therefore this tool can only be used with OpenSIPS versions
higher than 3.0. For older versions of OpenSIPS, use the old `opensipsctl`
tool from the `opensips` project.

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

If no configuration file is specified by the `-f|--config` parameter, OpenSIPS
CLI searches for one in the following locations, in this exact order:
`~/.opensips-cli.cfg`, `/etc/opensips-cli.cfg`, `/etc/opensips/opensips-cli.cfg`. If no file is found, it starts with the default configuration.

The OpenSIPS CLI core can use the following parameters:

* `prompt_name`: The name of the OpenSIPS CLI prompt (Default: `opensips-cli`)
* `prompt_intro`: Introduction message when entering the OpenSIPS CLI
* `prompt_emptyline_repeat_cmd`: Repeat the last command on an emptyline (Default: `False`)
* `history_file`: The path of the history file (Default: `~/.opensips-cli.history`)
* `history_file_size`: The backlog size of the history file (Default: `1000`)
* `log_level`: The level of the console logging (Default: `WARNING`)
* `communication_type`: Communication transport used by OpenSIPS CLI (Default: `fifo`)
* `fifo_file`: The OpenSIPS FIFO file to which the CLI will write commands
(Default: `/tmp/opensips_fifo`)
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

## Install

Forget about `opensipsctl` and move on to a pleasant console environment!

```
# required OS packages
sudo apt-get install python3 python3-pip python3-dev gcc default-libmysqlclient-dev # Debian & Ubuntu
sudo yum install python36 python36-pip python36-devel gcc mysql-devel # Red Hat & CentOS

# required Python3 packages
sudo pip3 install mysqlclient sqlalchemy sqlalchemy-utils pyOpenSSL

# download & install the CLI
git clone https://github.com/opensips/opensips-cli ~/src/opensips-cli
cd ~/src/opensips-cli
sudo python3 setup.py install clean

# enjoy!
opensips-cli
(opensips-cli): quit
```

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

This project is licensed under the GPL License - see the [LICENSE](LICENSE)
file for details.
