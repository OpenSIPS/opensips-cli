# Installation

`opensips-cli` is the intended convenient command-line interface for
administrating `opensips 3.x` installations.

Since `version 3.x`, the former script tool `opensipsctl` has been removed.
Its successor, `opensips-cli`, offers many advantages and will improve handling
for regular tasks in a pleasant console environment.

## From Packages

### Debian packages (.deb)

Add the ["cli-releases" repository from apt.opensips.org](https://apt.opensips.org/packages.php?v=cli)
to your system using the instructions provided, then install the
`opensips-cli` package.

Supported Operating Systems (at the time of writing):

* Debian 8-10
* Ubuntu 14.04, 16.04, 18.04, 19.04

### RPM packages (.rpm)

The ["opensips-yum-releases" meta-package from yum.opensips.org](https://yum.opensips.org/)
will install a repository that includes both `opensips` and `opensips-cli`
packages.  Once installed, install the `opensips-cli` package.

Supported Operating Systems (at the time of writing):

* RHEL 6-8, CentOS 6-8, Scientific Linux 6-8, Oracle Linux 6-8
* Fedora 27-31

### Arch Linux AUR

The distribution is managed as a rolling release.  Packages are administered
via the `pacman` front-end.  Please install the `opensips-cli` package from the
`AUR` using your favorite client:

```
# nightly build (latest `master` branch)
yay opensips-cli-git

# latest release branch
yay opensips-cli
```

## From Source Code

### Requirements

Before building the CLI, you need to install some dependencies.  The process
will vary on every supported operating system.

#### Debian / Ubuntu

```
# required OS packages
sudo apt install python3 python3-pip python3-dev gcc default-libmysqlclient-dev \
                 python3-mysqldb python3-sqlalchemy python3-sqlalchemy-utils \
                 python3-openssl

# alternatively, you can build the requirements from source
sudo pip3 install mysqlclient sqlalchemy sqlalchemy-utils pyOpenSSL
```

#### Red Hat / CentOS

```
# required OS packages
sudo yum install python36 python36-pip python36-devel gcc mysql-devel \
                 python36-mysql python36-sqlalchemy python36-pyOpenSSL

# alternatively, you can build the requirements from source
sudo pip3 install mysqlclient sqlalchemy sqlalchemy-utils pyOpenSSL
```

### Download, Build & Install

We can now download and install the latest development state from the GitHub
repository:

```
git clone https://github.com/opensips/opensips-cli ~/src/opensips-cli
cd ~/src/opensips-cli
sudo python3 setup.py install clean
```

### Cleaning up the install

To clean up the manually built and installed `opensips-cli` binary and package
files, run:

```
sudo rm -fr /usr/local/bin/opensips-cli /usr/local/lib/python3.6/dist-packages/opensipscli*
```

## Database Installation

Follow the [Database](modules/database.md#Examples) module documentation for a
complete guide.
