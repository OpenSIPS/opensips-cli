# OpenSIPS CLI - Instance module

This module can be used to list and switch different configuration sets
provisioned in the config file.

## Commands

This module exports the following commands:
* `show` - shows the current instance's name
* `list` - lists the instances available in the loaded configuration file
* `switch` - switches to a new instance

## Examples

Consider the following configuration file, which sets different prompts for
different instances:

```
[instance1]
prompt_name: instance-1

[instance2]
prompt_name: instance-2
```

Starting the OpenSIPS CLI without any parameter will start in the `default`
instance, but we can navigate afterwards through each provisioned instance:

```
$ opensips-cli -f instances.cfg
Welcome to OpenSIPS Command Line Interface!
(opensips-cli):
(opensips-cli): instance list
default
instance1
instance2
(opensips-cli): instance switch instance1
(instance-1): instance switch instance2
(instance-2): instance switch default
(opensips-cli):
```

One can also start OpenSIPS CLI with an instance parameter:

```
$ opensips-cli -f instances.cfg -i instance1
Welcome to OpenSIPS Command Line Interface!
(instance-1):
```

## Remarks

* The `default` instance is always available, even if not provisioned in the
configuration file. This is because the default config file is always loaded.
