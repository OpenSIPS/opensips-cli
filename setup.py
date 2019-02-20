#!/usr/bin/env python

"""
Installs OpenSIPS Command Line Interface
"""

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
print(setuptools.find_namespace_packages())

setuptools.setup(
    name = "opensipscli",
    version = "1.0.0",
    author = "OpenSIPS Project",
    author_email = "project@opensips.org",
    description = "OpenSIPS Command Line Interface",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/OpenSIPS/opensips-cli",
    packages = setuptools.find_namespace_packages(),
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
)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

