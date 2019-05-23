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

from opensipscli.module import Module
from opensipscli.logger import logger
from opensipscli.config import cfg
from opensipscli.db import (
    osdb, osdbError, osdbConnectError, osdbArgumentError, osdbNoSuchModuleError
)

import os

DEFAULT_DB_NAME = "opensips"
STANDARD_DB_MODULES = [
    "acc",
    "alias_db",
    "auth_db",
    "avpops",
    "clusterer",
    "dialog",
    "dialplan",
    "dispatcher",
    "domain",
    "drouting",
    "group",
    "load_balancer",
    "msilo",
    "permissions",
    "rtpproxy",
    "rtpengine",
    "speeddial",
    "tls_mgm",
    "usrloc"
]

class database(Module):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_path = None

    def __exclude__(self):
        if cfg.exists("database_url"):
            db_url = cfg.get("database_url")
            return not osdb.has_dialect(osdb.get_dialect(db_url))
        else:
            return not osdb.has_sqlalchemy()

    def get_migrate_scripts_path(self, db_schema):
        if self.db_path is not None:
            return [
                os.path.join(self.db_path, 'db-migrate',
                        'table-migrate.{}'.format(db_schema)),
                os.path.join(self.db_path, 'db-migrate',
                        'db-migrate.{}'.format(db_schema)),
                ]

    def get_schema_path(self, db_schema):
        if self.db_path is not None:
            return os.path.join(self.db_path, db_schema)

        db_path = cfg.read_param("database_path",
                "Please provide the path to the OpenSIPS DB scripts")
        if db_path is None:
            print()
            logger.error("don't know how to find the path to the OpenSIPS DB scripts")
            return None
        if not os.path.exists(db_path):
            logger.error("path '{}' to OpenSIPS DB scripts does not exist!".
                    format(db_path))
            return None
        if not os.path.isdir(db_path):
            logger.error("path '{}' to OpenSIPS DB scripts is not a directory!".
                    format(db_path))
            return None

        schema_path = os.path.join(db_path, db_schema)
        if not os.path.isdir(schema_path):
            logger.error("invalid OpenSIPS DB scripts dir: '{}'!".
                    format(schema_path))
            return None

        self.db_path = db_path
        return schema_path

    def do_drop(self, params=None):

        db_url = cfg.read_param("database_url",
                "Please provide us the URL of the database")
        if db_url is None:
            print()
            logger.error("no URL specified: aborting!")
            return -1

        if params and len(params) > 0:
            db_name = params[0]
        else:
            db_name = cfg.read_param("database_name",
                    "Please provide the database to drop",
                    DEFAULT_DB_NAME)

        db = osdb(db_url, db_name)

        # check to see if the database has already been created
        if db.exists():
            if cfg.read_param("database_force_drop",
                    "Do you really want to drop the '{}' database".
                        format(db_name),
                    False, True):
                db.drop()
            else:
                logger.info("database '{}' not dropped!".format(db_name))
        else:
            logger.warning("database '{}' does not exist!".format(db_name))

    def do_add(self, params):

        if len(params) < 1:
            logger.error("No module to add added")
            return -1
        module = params[0]

        db_url = cfg.read_param("database_url",
                "Please provide us the URL of the database")
        if db_url is None:
            print()
            logger.error("no URL specified: aborting!")
            return -1

        if len(params) < 2:
            db_name = cfg.read_param("database_name",
                    "Please provide the database to add the module to",
                    DEFAULT_DB_NAME)
        else:
            db_name = params[1]


        db = osdb(db_url, db_name)

        if not db.exists():
            logger.warning("database '{}' does not exist!".format(db_name))
            return -1

        db_schema = db.dialect
        schema_path = self.get_schema_path(db_schema)
        if schema_path is None:
            return -1

        module_file_path = os.path.join(schema_path,
                "{}-create.sql".format(module))
        if not os.path.isfile(module_file_path):
            logger.warning("cannot find OpenSIPS DB file: '{}'!".
                    format(module_file_path))
            return -1

        db.use()
        try:
            db.create_module(module_file_path)
        except osdbError as ex:
            logger.error("cannot import: {}".format(ex))
            return -1

        db.destroy()
        logger.info("Module {} has been successfully added!".
                format(module))
        return 0

    def do_create(self, params=None):

        db_url = cfg.read_param("database_url",
                "Please provide us the URL of the database")
        if db_url is None:
            print()
            logger.error("no URL specified: aborting!")
            return -1

        if params and len(params) > 0:
            db_name = params[0]
        else:
            db_name = cfg.read_param("database_name",
                    "Please provide the database to create",
                    DEFAULT_DB_NAME)

        db = osdb(db_url, db_name)
        self._do_create(db)
        db.destroy()

        return 0

    def _do_create(self, db, db_name=None, do_all_tables=False):
        if db_name is None:
            db_name = db.db_name

        # check to see if the database has already been created
        if db.exists(db_name):
            logger.error("database '{}' already exists!".format(db_name))
            return -2

        db_schema = db.db_url.split(":")[0]
        schema_path = self.get_schema_path(db_schema)
        if schema_path is None:
            return -1

        standard_file_path = os.path.join(schema_path, "standard-create.sql")
        if not os.path.isfile(standard_file_path):
            logger.error("cannot find stardard OpenSIPS DB file: '{}'!".
                    format(standard_file_path))
            return -1
        tables_files = [ standard_file_path ]

        # all good now - check to see what tables we shall deploy
        if cfg.read_param(None,
                "Create [a]ll tables or just the [c]urrently configured ones?",
                default="a").lower() == "a":
            print("Creating all tables ...")
            tables = [ f.replace('-create.sql', '') \
                        for f in os.listdir(schema_path) \
                        if os.path.isfile(os.path.join(schema_path, f)) and \
                            f != 'standard-create.sql' ]
        else:
            print("Creating the currently configured set of tables ...")
            if cfg.exists("database_modules"):
                tables = cfg.get("database_modules").split(" ")
            else:
                tables = STANDARD_DB_MODULES

        logger.debug("deploying tables {}".format(" ".join(tables)))
        for table in tables:
            if table == "standard":
                # already checked for it
                continue
            table_file_path = os.path.join(schema_path,
                    "{}-create.sql".format(table))
            if not os.path.isfile(table_file_path):
                logger.warn("cannot find file to create {}: {}".
                        format(table, table_file_path))
            else:
                tables_files.append(table_file_path)

        db.create(db_name)
        db.use(db_name)

        for table_file in tables_files:
            print("Running {}...".format(os.path.basename(table_file)))
            try:
                db.create_module(table_file)
            except osdbError as ex:
                logger.error("cannot import: {}".format(ex))

        print("The '{}' database has been successfully created!".format(db_name))

    def do_migrate(self, params):
        if len(params) < 2:
            logger.error("Usage: database migrate <old-database> <new-database>")
            return 0

        old_db = params[0]
        new_db = params[1]

        db_url = cfg.read_param("database_url",
                "Please provide the URL of the database")
        if db_url is None:
            print()
            logger.error("no URL specified, aborting!")
            return -1

        try:
            db = osdb(db_url, old_db)
        except osdbArgumentError:
            logger.error("Bad URL, it should resemble: backend://user:pass@hostname")
            return
        except osdbConnectError:
            logger.error("Failed to connect to database!")
            return
        except osdbNoSuchModuleError:
            logger.error("This database is not supported!")
            return

        if not db.exists(old_db):
            logger.error("the source database ({}) does not exist!".format(old_db))
            return -2

        print("Creating database {}...".format(new_db))
        self._do_create(db, new_db)

        db_schema = db.db_url.split(":")[0]
        migrate_scripts = self.get_migrate_scripts_path(db_schema)
        if migrate_scripts is None:
            return -1

        logger.debug("Got path: {}".format(migrate_scripts))

        print("Migrating all matching OpenSIPS tables...")
        db.migrate(migrate_scripts, old_db, new_db)

        print("Successfully copied all OpenSIPS table data into the '{}' database!".format(
                    new_db))

        db.destroy()
        return 0
