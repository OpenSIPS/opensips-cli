Summary:  Interactive command-line tool for OpenSIPS 3.0+
Name:     opensips-cli
Version:  0.2
Release:  0%{?dist}
License:  GPL-3+
Group:    System Environment/Daemons
Source0:  Source0:  http://download.opensips.org/cli/%{name}-%{version}.tar.gz
URL:      http://opensips.org

BuildArch: noarch

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-rpm-macros
BuildRequires:  mysql-devel
BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

AutoReqProv: no

Requires: python3
%if 0%{?rhel} == 7
Requires: python36-sqlalchemy
Requires: python36-mysql
Requires: python36-pyOpenSSL
%else
Requires: python3-sqlalchemy
Requires: python3-mysqlclient
Requires: python3-pyOpenSSL
%endif

%description
This package contains the OpenSIPS CLI tool, an interactive command line tool
that can be used to control and monitor OpenSIPS 3.0+ servers.
.
OpenSIPS is a very fast and flexible SIP (RFC3261)
server. Written entirely in C, OpenSIPS can handle thousands calls
per second even on low-budget hardware.
.
C Shell-like scripting language provides full control over the server's
behaviour. Its modular architecture allows only required functionality to be
loaded.
.
Among others, the following modules are available: Digest Authentication, CPL
scripts, Instant Messaging, MySQL support, Presence Agent, Radius
Authentication, Record Routing, SMS Gateway, Jabber/XMPP Gateway, Transaction
Module, Registrar and User Location, Load Balaning/Dispatching/LCR,
XMLRPC Interface.

%prep
%autosetup -n %{name}-%{version}

%build
%py3_build

%install
%py3_install

%clean
rm -rf $RPM_BUILD_ROOT

%files
%{_bindir}/opensips-cli
%{python3_sitelib}/opensipscli/*
%{python3_sitelib}/opensipscli-*.egg-info
%doc README.md
%doc docs/*
%doc etc/default.cfg
%license LICENSE

%changelog
* Thu Aug 27 2020 Liviu Chircu <liviu@opensips.org> - 0.1-2
- Update package summary.
* Fri Jan 3 2020 Nick Altmann <nick.altmann@gmail.com> - 0.1-1
- Initial spec.
