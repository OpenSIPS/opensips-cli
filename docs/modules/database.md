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
* `migrate` - copy and convert an OpenSIPS database into its next OpenSIPS
release equivalent

## Configuration

### Database Schema Files

The database schema files for each supported SQL backend can be installed via
their corresponding OpenSIPS client module package.  For example (only install modules useful to you):

```
apt install opensips-mysql-module opensips-postgres-module opensips-sqlite-module opensips-berkeley-module
yum install opensips-mysql-module opensips-postgres-module opensips-sqlite-module opensips-berkeley-module
```

Once installed, the schema files will be auto-detected by `opensips-cli`.

### Setting up the `database` module

The following parameters are allowed in the config file:

* `database_schema_path` (optional) - absolute path to the OpenSIPS DB schema directory,
usually `/usr/share/opensips` if installed from packages or `/path/to/opensips/scripts` if you
are using the OpenSIPS source tree.  Default: `/usr/share/opensips`
* `database_admin_url` (optional) - a connection string to the database with privileged
(administrator) access level which will be used to create/drop databases, as
well as to create or ensure access for the non-privileged DB access user
provided via `database_url`.  The URL combines schema, username, password, host
and port.  Default: `mysql://root@localhost`.
* `database_url` (optional) - the connection string to the database.  A good practice
would be to use a non-administrator access user for this URL.  Default:
`mysql://opensips:opensipsrw@localhost`.
* `database_name` (optional) - the name of the database.  Modules may be separately added
to this database if you choose not to install all of them.  Default: `opensips`.
* `database_modules` (optional) - accepts the `ALL` keyword that indicates all the
available modules should be installed, or a space-separated list of modules
names.  If processed with the `create` command, the corresponding tables will
be deployed.  Default: `acc alias_db auth_db avpops clusterer dialog
dialplan dispatcher domain drouting group load_balancer msilo permissions
rtpproxy rtpengine speeddial tls_mgm usrloc`.
* `database_force_drop` (optional) - indicates whether the `drop` command will drop the
database without user interaction.  Default: `false`

## Usage Examples

### Database Management

Consider the following configuration file:

```
[default]
#database_modules: acc clusterer dialog dialplan dispatcher domain rtpproxy usrloc
database_modules: ALL

#database_admin_url: postgresql://root@localhost
database_admin_url: mysql://root@localhost
```

The following command will create the `opensips` database and all possible
tables within the MySQL instance.  Additionally, the `opensips:opensipsrw` user
will be created will `ALL PRIVILEGES` for the `opensips` database.  For some
backends, such as PostgreSQL, any additionally required permissions will be
transparently granted to the `opensips` user, for example: table-level or
sequence-level permissions.

```
opensips-cli -x database create
Password for admin DB user (root): _
```

If we want to add a new module, say `rtpproxy`, we have to run:

```
opensips-cli -x database add rtpproxy
```
The command above will create the `rtpproxy_sockets` table.

A drop command will prompt the user whether they really want to drop the
database or not:

```
$ opensips-cli -x database drop
Do you really want to drop the 'opensips' database [Y/n] (Default is n): n
```

But setting the `database_force_drop` parameter will drop it without asking:
```
opensips-cli -o database_force_drop=true -x database drop
```

### Database Migration (MySQL only)

The `database migrate` command can be used to _incrementally_ upgrade
your OpenSIPS database.

#### Migrating from 2.4 to 3.0

```
# fetch the 3.0 OpenSIPS repo & migration scripts
git clone https://github.com/OpenSIPS/opensips -b 3.0 ~/src/opensips-3.0

# provide the custom path to the migration scripts and perform the migration
opensips-cli -o database_schema_path=~/src/opensips-3.0/scripts \
             -x database migrate 2.4_to_3.0 opensips_2_4 opensips_mig_3_0
```

#### Migrating from 3.0 to 3.1

```
# fetch the 3.1 OpenSIPS repo & migration scripts
git clone https://github.com/OpenSIPS/opensips -b 3.1 ~/src/opensips-3.1

# provide the custom path to the migration scripts and perform the migration
opensips-cli -o database_schema_path=~/src/opensips-3.1/scripts \
             -x database migrate 3.0_to_3.1 opensips_3_0 opensips_mig_3_1
```

## Dependencies

* [sqlalchemy and sqlalchemy_utils](https://www.sqlalchemy.org/) - used to
abstract the SQL database regardless of the backend used

## Limitations

This module can only manipulate database backends that are supported by the
[SQLAlchemy](https://www.sqlalchemy.org/) project, such as  SQLite,
Postgresql, MySQL, Oracle, MS-SQL.
