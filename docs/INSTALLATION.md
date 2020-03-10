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
via the `pacman`front-end. Please install `opensips-cli` from the `AUR` using
your favorite client:

```
# git branch
yay opensips-cli-git

# release branch
yay opensips-cli
```
### Source code / Master Branch

The latest development state can be downloaded and installed from the GitHub
repository.

```
git clone https://github.com/opensips/opensips-cli ~/src/opensips-cli
cd ~/src/opensips-cli
sudo python3 setup.py install clean
```

## Database Installation

Follow the [Database](modules/database.md#Examples) module documentation for a
complete guide.
