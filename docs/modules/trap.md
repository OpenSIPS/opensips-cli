# OpenSIPS CLI - Trap module

Using this module you can create a trap file of the OpenSIPS processes.
When running without any parameters, the `trap` module fetches the OpenSIPS
pids by issuing an `mi ps` command. However, the pids of OpenSIPS can be
specified as additional parameters to the `trap` command.

## Configuration

This module can have the following parameters specified through a config file:
* `trap_file` - name of the file that will contain the trap (Default is
`/tmp/gdb_opensips_$(date +%Y%m%d_%H%M%S)`).

## Examples

Trapping OpenSIPS with pids specified through MI:

```
opensips-cli -x trap
```

When OpenSIPS is stuck and cannot be trapped, because you cannot run MI
commands, you can specify the OpenSIPS pids you want to trap directly in the
cli:

```
opensips-cli -x trap 5113 5114 5115 5116
```

## Remarks

* This module only works when `opensips-cli` is ran on the same machine as
OpenSIPS, since it needs direct access to OpenSIPS processes.
* This module requires to have the `gdb` command in system's `PATH`. At
startup, it checks if `gdb` can be located (using `which`), and if it cannot,
the module becomes unavailable.
* You need administrative priviledges to run the `trap`.
