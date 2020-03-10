# OpenSIPS CLI - Database module

Module used to manipulate the database used by OpenSIPS.

## Commands

This module exports the following commands:
* `create` - creates a new database. Can receive an optional parameter,
specifying the name of the database to be created. This command also deploys
the standard OpenSIPS table, as well as other standard tables
* `drop` - drops a database. Can receive an optional parameter, specifying
which database to delete.
* `add` - adds a new module's tables in an existing database. Receives as
parameter the name of the module, as specified in the OpenSIPS scripts
hierarchy.
* `migrate` - copy and convert an OpenSIPS 2.4 database into its OpenSIPS
3.0 equivalent

## Configuration

## Database Schema Files

The database schema files for each supported SQL backend can be installed via
their corresponding OpenSIPS client module package.  For example (only install modules useful to you):

```
apt install opensips-mysql-module opensips-postgres-module opensips-sqlite-module opensips-berkeley-module
yum install opensips-db_mysql opensips-db_postgresql opensips-db_sqlite opensips-db_berkeley
```

Once installed, the schema files will be auto-detected by `opensips-cli`.

## Setting up the `database` module

The following parameters are allowed in the config file:

* `database_schema_path` - the directory to the OpenSIPS DB schema files,
usually `/usr/share/opensips` if installed from packages or `./scripts` if you
are using the OpenSIPS source tree.
* `database_admin_url` - a connection string to the database with privileged
(administrator) access level which will be used to create/drop databases, as
well as to create or ensure access for the non-privileged DB access user
provided via `database_url`.  The URL combines schema, username, password, host
and port.  Default: `mysql://root@localhost`.
* `database_url` - the connection string to the database.  A good practice
would be to use a non-administrator access user for this URL.  Default:
`mysql://opensips:opensipsrw@localhost`.
* `database_name` - the name of the database. Modules may be created, dropped
or added to this database.  Default: `opensips`.
* `database_modules` - accepts the `ALL` keyword that indicates all the
available modules should be installed, or a space-separated list of modules
names.  If processed with the `create` command, the corresponding tables will
be deployed.  Default modules: `acc alias_db auth_db avpops clusterer dialog
dialplan dispatcher domain drouting group load_balancer msilo permissions
rtpproxy rtpengine speeddial tls_mgm usrloc`.
* `database_force_drop` - indicates whether the `drop` command will drop the
database without user interaction.

## Examples

Consider the following configuration file:

```
[default]
database_admin_url: mysql://root:secret@localhost
database_modules: dialog usrloc

# optional DB override instance, invoked using `opensips-cli -i postgres ...`
[postgres]
database_url: postgres://opensipspg:opensipspgrw@localhost
database_admin_url: postgres://root:secret@localhost
database_modules: dialog usrloc
```

The following command will create the `opensips` database, containing only the
`version`, `dialog` and `location` tables (according to the `database_modules`
parameter).  Additionally, the `opensips:opensipsrw` user will be created will
`ALL PRIVILEGES` for the `opensips` database.

For some backends, such as PostgreSQL, any additionally required permissions
will be transparently granted to the `opensips` user, for example:
table-level or sequence-level permissions.

```
opensips-cli -x database create
```

If we want to add a new module, say `rtpproxy`, we have to run:

```
opensips-cli -x database add rtpproxy
```
The command above will create the `rtpproxy_sockets` table.

A drop command will prompt the user whether he really wants to drop the
database or not:

```
$ opensips-cli -x database drop
Do you really want to drop the 'opensips' database [Y/n] (Default is n): n
```

But setting the `database_force_drop` parameter will drop it without asking:
```
opensips-cli -o database_force_drop=true -x database drop
```

## Dependencies

* [sqlalchemy and sqlalchemy_utils](https://www.sqlalchemy.org/) - used to
abstract the SQL database regardless of the backend used

## Limitations

This module can only manipulate database backends that are supported by the
[SQLAlchemy](https://www.sqlalchemy.org/) project, such as  SQLite,
Postgresql, MySQL, Oracle, MS-SQL.
