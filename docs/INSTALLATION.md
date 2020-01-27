# Installation

`opensips-cli` is the intended convenient command-line interface for
administrating `opensips 3.x` installations.

Since `version 3.x`, the former script tool `opensipsctl` has been removed.
Its successor, `opensips-cli`, offers many advantages and will improve
handling for regular tasks in a pleasant console environment.

A non-exclusive list with its eye-catching features:

* modular design
* JSON-RPC based Management Interface
* auto completion
* forward/reverse history search
* Python based (e.g use of inheritance)

## General

To make use of `opensips-cli`, you need to install the tool itself as well as
its dependencies. The process will vary on every supported operating system.

In all cases, the installation process will create a default configuration.
This will be stored in `/etc/opensips/opensips-cli.cfg` and serves as the
system default (reference: [Core](../etc/default.cfg),
[Database](modules/database.md#Examples).
No security sensible data (e.g. passwords) should be saved in this file.
If needed, you may copy this default to your home-directory
(e.g. ~home/opensips-cli.cfg), change the access rights (e.g. `chmod 0600`) and
adopt the parameter as needed.  `opensips-cli` will respect the presence of
that file in favor of the system default.

### Distribution packages

There are several recompiled packages, ready for your distribution.

#### Debian / Ubuntu

Both distributions support `*.deb` based packages, administered
using the `apt` front-end:

```
# required OS packages
sudo apt install python3 python3-pip python3-dev gcc default-libmysqlclient-dev

# required Python3 packages
sudo pip3 install mysqlclient sqlalchemy sqlalchemy-utils pyOpenSSL
```

#### Red Hat / CentOS

Both distributions support `*.rpm` based packages, administered
using the `yum` front-end:

```
# required OS packages
sudo yum install python36 python36-pip python36-devel gcc mysql-devel

# required Python3 packages
sudo pip3 install mysqlclient sqlalchemy sqlalchemy-utils pyOpenSSL
```

#### Arch-Linux

The distribution is managed as a rolling relase. Packages are administered
via the `pacman`front-end. Please install `opensip-cli` from the `AUR` using
your favorite client:

```
# git branch
yay opensip-cli-git

# release branch
yay opensip-cli
```
### Source code / Master Branch

The latest development state can be downloaded and installed from the GitHub
repository.

```
git clone https://github.com/opensips/opensips-cli ~/src/opensips-cli
cd ~/src/opensips-cli
sudo python3 setup.py install clean
```

## Backend specific

### MySQL

TODO: describe needed MySQL / MariaDB specific steps

### PostgresSQL

To create a new PostgreSQL database, the calling user needs to
have suitable access privileges.

#### authentication mechanism
Client authentication is controlled by a configuration file
<a href=<https://www.postgresql.org/docs/12.1/auth-pg-hba-conf.html>(pg_hba.conf)</a>.
Per default this file is stored in the database cluster's data directory
(/var/lib/postgres/data). Connecting via Unix domain sockets, as well
as ipv4 and ipv6 sessions, are usually granted for all local users accessing
the local host. Per default the session will be authenticated utilizing
auth-method `trusted`.

The `trusted` method allows anyone that can connect to the PostgreSQL
database server to login as any PostgreSQL user.
This is fine, since PostgreSQL users are handled internally and are not
connected to system accounts. It is a common good habit, to leave the
system user `postgres` locked! You never want to set its password.
All fine tuning is taking place inside the PostgreSQL Roles and Privileges
subsystem.

Access privileges will be assigned to roles via the
<a href=https://www.postgresql.org/docs/12.1/sql-grant.html>grant</a>
methods. The GRANT command has two basic variants:

* one that grants privileges on a database object
* one that grants membership in a role

#### opensips-cli methods

To install a new database with `opensips-cli`, the method `database create`
is used . If the calling PostgreSQL user is associated to a role that includes
the `CREATE` privilege, you are fine. The creation will use the `template_uri`,
connect to the database template ("template1") and traverse the following
steps:

* create a new database instance (default: "opensips")
* create a new PostgreSQL user (default: "opensips")
* assign a password to the new PostgreSQL user (default: "opensipspw")
* create a new role (default: "opensips")
* associated correct privileges to this role:
  (default: "NOCREATEDB", "NOCREATEROLE", "LOGIN", "REPLICATION")
* associate new role with new PostgreSQL user

Once completed, `opensips` and `opensips-cli`
will connect to the database using the general `database_url`.

starting opensips-cli in interactive mode will allow to auto-complete available methods:

```
opensips
(opensips-cli): database
add            create         create_module  drop           get_role
alter_role     create_db      create_role    drop_role      migrate
(opensips-cli): quit
```

#### admin tasks

If you take advantage of `opensips-cli` non-interactive installation procedure
that offers `zero configuration`, we encourage the admin to adopt the default
password.

```
# example call:
# sudo -u postgres opensips-cli -i postgres -x database create
```
