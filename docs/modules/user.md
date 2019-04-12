# OpenSIPS CLI - User module

Module used to add/remove/update user information in OpenSIPS tables.

## Commands

This module exports the following commands:
* `add` - adds a new username in the database; accepts an optional user
(with or without a domain) as parameter, followed by a password. If any of
them are missing, you will be prompted for
* `password` - changes the password of an username; accepts similar parameters
as `add`
* `delete` - removes an username from the database; accepts the user as
parameter

## Configuration

The parameters from this tool can be either provisioned in the configuration
file, either prompted for during runtime, similar to the `database` module.
If a parameter is specified in the configuration file, you will not be
prompted for it!

These are the parameters that can be specified in the config file:
* `domain` - the domain of the username; this is only read/prompted for when
the user to be added/deleted does not already have a domain part
`scripts/` directory in the OpenSIPS source tree, or `/usr/share/opensips/`
* `plain_text_passwords` - indicates whether passwords should be stored in
plain-text, or just the `ha1` and `ha1b` values. Defaults to `false`

## Examples

Add the `username@domain.com` user with the `S3cureP4s$` password.

```
opensips-cli -x user add username@domain.com S3cureP4s$
```

If the domain, or password is not specified, it will be prompted:

```
(opensips-cli): user add razvan
Please provide the domain of the user: domain.com
Please enter new password:
Please repeat the password:
```
A similar behavior is for the `delete` and `passwords` commands, where you
will be prompted for the missing/necessary information.

To remove an username, use the `delete` command:
```
opensips-cli -x user delete username@domain.com
```

## Dependencies

* [sqlalchemy and sqlalchemy_utils](https://www.sqlalchemy.org/) - used to
abstract the database manipulation, regardless of the backend used

## Limitations

This module can only manipulate database backends that are supported by the
[SQLAlchemy](https://www.sqlalchemy.org/) project, such as  SQLite,
Postgresql, MySQL, Oracle, MS-SQL.
