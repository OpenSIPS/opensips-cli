# OpenSIPS CLI - Database module

Module used to manipulate the database used by OpenSIPS.

## Commands

This module provides commands, that will handle common database tasks in an
engine agnostic way. Thus, you can use them for any supported database backend.

Given the nature of database backends, they do have 'dialect' specific concepts.
Thus, the commands need to be grouped in 'non dialect specific' and 'dialect
specific' commands. Dialect specific commands only take effect, if OpenSIPS CLI
will detect the underlying backend.

### Non dialect specific commands

* `create` - creates a new database. Can receive an optional parameter,
specifying the name of the database to be created. This command also deploys
the standard OpenSIPS table, as well as other standard tables
* `drop` - drops a database. Can receive an optional parameter, specifying
which database to delete.
* `add` - adds a new module's tables in an existing database. Receives as
parameter the name of the module, as specified in the OpenSIPS scripts
hierarchy.

### Dialect specific commands

* `create_role` - creates a role. Can receive an optional parameter,
specifying the name of the role to be created.
* `drop_role` - drops a role. Can receive an optional parameter,
specifying the name of the role to be created.
* `grant_db_options` - grant options for a given role on the database.
Can receive an optional list, specifying the options that should be assigned
to the given role (defaults to 'ALL PRIVILEGES')
* `get_role` - show list of options assigned to a given role.

## Configuration

The parameters from this tool can be either provisioned in the configuration
file, either prompted for during runtime. If a parameter is specified in the
configuration file, you will not be prompted for it!

These are the parameters that can be specified in the config file:
* `database_path` - the directory to the OpenSIPS DB scripts, usually the
`scripts/` directory in the OpenSIPS source tree, or `/usr/share/opensips/`
* `database_url` - an URL to the database, containing schema, username,
password, host and port. Example: `mysql://user:password@host`
* `database_name` - the name of the database to create, drop, or add modules
to
* `database_modules` - a space-separated list of the modules tables that need
to be deployed by the `create` command. Defaults are: `acc alias_db auth_db
avpops clusterer dialog dialplan dispatcher domain drouting group
load_balancer msilo permissions rtpproxy rtpengine speeddial tls_mgm usrloc`
* `database_force_drop` - indicates whether the `drop` command should drop the
database without prompting the user
* `template_name` - the name of the database template, that is used to handle
role specific commands (defaults to 'template1').
* `role_name` - the name of the role. This role will be assigned to the OpenSIPS
database, inheriting the rights and general database options.
* `role_options` - the options that should be assigned to the given `role_name`.
Per default following options will be assinged ("NOCREATEDB", "NOCREATEROLE",
"LOGIN", "REPLICATION")
* `role_force_drop` - indicates whether the `drop_role` command should drop the
given role without prompting the user

## Examples

Consider the following configuration file:

```
[default]
database_url=mysql://root@localhost
database_name=opensips
database_modules=dialog usrloc
template_name=template1
role_name=opensips
```

The following command will create the `opensips` table, containing only the
`version`, `dialog` and `location` tables (according to the `database_modules`
parameter). In case you are using a backend that supports the 'role' concept
(eg. PostgreSQL), the role `opensips` will be created in line. As inherited
from the role options, `opensips` will hold all rights to handle database
tasks, including the right to login:

```
opensips-cli -x database create
```

If we want to add a new module, let's say `rtpproxy`, we have to run:

```
opensips-cli -x database add rtpproxy
```

The command above will create the `rtpproxy_sockets` table.

A drop command will prompt the user whether he really wants to drop the
database or not:

```
$ opensips-cli -x database drop
Do you really want to drop the 'opensips_cli' database [Y/n] (Default is n): n
```

But setting the `database_force_drop` parameter will drop it without asking:
```
opensips-cli -o database_force_drop=true -x database drop
```

In case you are using a backend that supports the 'role' concept
(eg. PostgreSQL), the role `opensips` isn't needed any longer. You will be
asked, if it should be dropped in line.

```
Do you really want to drop the 'opensips' role [Y/n] (Default is n): n
```

If you set `role_force_drop` parameter in the config file, the role will be drop
it without asking:

```
opensips-cli -o database_force_drop=true -o role_force_drop=true -x database drop
```

## Dependencies

* [sqlalchemy and sqlalchemy_utils](https://www.sqlalchemy.org/) - used to
abstractizeze the database manipulation, regardless the backend used

## Limitations

This module can only manipulate database backends that are supported by the
[SQLAlchemy](https://www.sqlalchemy.org/) project, such as  SQLite,
Postgresql, MySQL, Oracle, MS-SQL.
