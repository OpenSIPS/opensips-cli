#!/usr/bin/env python
##
## This file is part of OpenSIPS CLI
## (see https://github.com/OpenSIPS/opensips-cli).
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program. If not, see <http://www.gnu.org/licenses/>.
##

"""
Installs OpenSIPS Command Line Interface
"""

import os
try:
    from setuptools import setup, Command
except ImportError:
    from distutils.core import setup, Command
from opensipscli import defaults

with open("README.md", "r") as fh:
    long_description = fh.read()

class CleanCommand(Command):
    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        os.system('rm -vrf ./build ./dist ./*.pyc ./*.tgz ./*.egg-info')

setup(
    name = "opensipscli",
    version = defaults.VERSION,
    author = "OpenSIPS Project",
    author_email = "project@opensips.org",
    maintainer = "Razvan Crainea",
    maintainer_email = "razvan@opensips.org",
    description = "OpenSIPS Command Line Interface",
    long_description = long_description,
    url = "https://github.com/OpenSIPS/opensips-cli",
    download_url = "https://github.com/OpenSIPS/opensips-cli/archive/master.zip",
    packages = [
        "opensipscli",
        "opensipscli.modules",
        "opensipscli.communication"
    ],
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    scripts = [
        "bin/opensips-cli"
    ],
    project_urls = {
        "Source Code": "https://github.com/OpenSIPS/opensips-cli",
        "Issues Tracker": "https://github.com/OpenSIPS/opensips-cli/issues",
    },
    cmdclass={
        'clean': CleanCommand,
    }
)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

