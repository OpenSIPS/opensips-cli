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
    osdb, osdbError, osdbConnectError,
    osdbArgumentError, osdbNoSuchModuleError
)

import os
from getpass import getpass

DEFAULT_DB_TEMPLATE = "template1"
DEFAULT_DB_NAME = "opensips"
DEFAULT_ROLE_NAME = "opensips"
DEFAULT_ROLE_OPTIONS = [
    "NOCREATEDB",
    "NOCREATEROLE",
    "LOGIN",
    "REPLICATION"
]

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

EXTRA_DB_MODULES = [
    "b2b",
    "b2b_sca",
    "call_center",
    "carrierroute",
    "closeddial",
    "clp",
    "domainpolicy",
    "emergency",
    "fraud_detection",
    "freeswitch_scripting",
    "imc",
    "load_balancer",
    "presence",
    "registrant",
    "rls",
    "smpp",
    "tracer",
    "userblacklist"
]

SUPPORTED_BACKENDS = [
    "mysql",
    "postgres",
    "sqlite",
    "oracle",
]

MIGRATE_TABLES_24_TO_30 = [
    'registrant', # changed in 3.0
    'tls_mgm',    # changed in 3.0
    'acc',
    'address',
    'cachedb',
    'carrierfailureroute',
    'carrierroute',
    'cc_agents',
    'cc_calls',
    'cc_cdrs',
    'cc_flows',
    'closeddial',
    'clusterer',
    'cpl',
    'dbaliases',
    'dialplan',
    'dispatcher',
    'domain',
    'domainpolicy',
    'dr_carriers',
    'dr_gateways',
    'dr_groups',
    'dr_partitions',
    'dr_rules',
    'emergency_report',
    'emergency_routing',
    'emergency_service_provider',
    'fraud_detection',
    'freeswitch',
    'globalblacklist',
    'grp',
    'imc_members',
    'imc_rooms',
    'load_balancer',
    'location',
    'missed_calls',
    'presentity',
    'pua',
    're_grp',
    'rls_presentity',
    'rls_watchers',
    'route_tree',
    'rtpengine',
    'rtpproxy_sockets',
    'silo',
    'sip_trace',
    'smpp',
    'speed_dial',
    'subscriber',
    'uri',
    'userblacklist',
    'usr_preferences',
    'xcap',
    ]


class database(Module):
    """
    Class: database modules
    """
    def __init__(self, *args, **kwargs):
        """
        Constructor
        """
        super().__init__(*args, **kwargs)
        self.db_path = None

    def __complete__(self, command, text, line, begidx, endidx):
        """
        helper for autocompletion in interactive mode
        """
        role_commands = (
            'alter_role',
            'create_role',
            'drop_role',
            'get_role')

        if command == 'create':
            db_name = ['opensips', 'opensips_test']
            if not text:
                return db_name
            ret = [t for t in db_name if t.startswith(text)]
        elif command == 'create_module':
            module_name = ['b2b', 'b2b_sca', 'call_center', 'carrierroute', 'closeddial',
                           'clp', 'domainpolicy', 'emergency', 'fraud_detection', 'freeswitch_scripting',
                           'imc', 'load_balancer', 'presence', 'registrant', 'rls', 'smpp',
                           'tracer', 'userblacklist']
            if not text:
                return module_name
            ret = [t for t in module_name if t.startswith(text)]
        elif command == 'migrate':
            db_source = ['opensips']
            if not text:
                return db_source
            ret = [t for t in db_source if t.startswith(text)]

            db_dest = ['opensips_new']
            if not text:
                return db_dest
            ret = [t for t in db_dest if t.startswith(text)]

        elif command in role_commands:
            role_name = ['opensips', 'opensips_role']
            if not text:
                return role_name
            ret = [t for t in role_name if t.startswith(text)]

        return ret if ret else ['']

    def __exclude__(self):
        """
        method exlusion list
        """
        if cfg.exists("database_url"):
            db_url = cfg.get("database_url")
            return not osdb.has_dialect(osdb.get_dialect(db_url))
        else:
            return not osdb.has_sqlalchemy()

    def __get_methods__(self):
        """
        methods available for autocompletion
        """
        return ['', 'add', 'alter_role',
				'create', 'create_db', 'create_module', 'create_role',
                'drop', 'drop_role', 'get_role', 'migrate']

    def ask_db_url(self):
        db_url = cfg.read_param("template_url",
             "Please provide the URL of the SQL database")
        if db_url is None:
            print()
            logger.error("no URL specified: aborting!")
            return -1

        return db_url

    #def __invoke__(self, cmd, params=None):
    #    """
    #    methods handles to preset defaults
    #    """
    #    if cmd is None:
    #        return self.diagnosis_summary()
    #    if cmd == 'create_role':
    #        #if not params:
    #            #params = ['role_name', 'role_options']
    #            #params = ['opensips', 'NOCREATEDB NOCREATEROLE LOGIN REPLICATION']
    #        return self.do_create_role(params)
    #    if cmd == 'drop_role':
    #        return self.do_drop_role(params)
    #    if cmd == 'get_role':
    #        return self.do_get_role()

    def do_add(self, params):
        """
        add a given table to the database (connection via URL)
        """
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

        # create an object store database instance
        db = self.get_db(db_url, db_name)
        if db is None:
            return -1

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

        db.connect(db_name)
        try:
            db.create_module(module_file_path)
        except osdbError as ex:
            logger.error("cannot import: {}".format(ex))
            return -1

        db.destroy()

        logger.info("Module {} has been successfully added!".
            format(module))

        return True

    def do_alter_role(self, params=None):
        """
        alter role attributes (connect to given template database)
        """

        db_url = cfg.read_param("template_url",
            "Please provide the URL to connect as template")

        if db_url is None:
            logger.error("no URL specified: aborting!")
            return -1

        db_template = cfg.read_param("database_template",
            "Please provide the database template name",
            DEFAULT_DB_TEMPLATE)
        if db_template is None:
            logger.error("no URL specified: aborting!")
            return -1

        # create an object store database instance
        db = self.get_db(db_url, db_template)
        if db is None:
            return -1

        role_name = None
        role_options = None
        role_password = None

        if len(params) > 0:
            role_name = ''.join(params[0])

        if role_name is None:
            role_name = cfg.read_param("role_name",
                "Please provide the role name to alter",
                DEFAULT_ROLE_NAME)
            logger.debug("role_name: '%s'", role_name)

        if db.exists_role(role_name) is True:
            if len(params) > 1:
                role_options = params[1]
            if len(params) > 2:
                role_password = params[2]

            if role_options is None:
                role_list = cfg.read_param("role_options",
                    "Please adapt the role options to alter",
                    DEFAULT_ROLE_OPTIONS)
                if len(role_list) > 0:
                    role_options = ' '.join(role_list)
                logger.debug("role_options: '%s'", role_options)

            if role_password is None:
                role_password = getpass("New password: ")
                logger.debug("role_password: '%s'", role_password)

            if db.alter_role(role_name, role_options, role_password) is False:
                logger.error("alter role '%s' didn't succeed", role_name)
                db.destroy()
        else:
            logger.warning("can't alter non existing role '%s'", role_name)

    def do_create(self, params=None):
        """
        create database with role-assigment and tables
        """

        if len(params) >= 1:
            db_name = ''.join(params[0])
        else:
            db_name = cfg.read_param("database_name",
                "Please provide the database to create",
                DEFAULT_DB_NAME)
        logger.debug("db_name: '%s'", db_name)

        db_url = self.ask_db_url()
        if db_url is None:
            return -1

        if self._do_create_db([db_name], db_url) < 0:
            return -1
        if self.create_tables(db_name, db_url=db_url) < 0:
            return -1

        return 0

    def do_create_db(self, params=None):
        return self._do_create_db(params)

    def _do_create_db(self, params=None, db_url=None):
        """
        create database and roles assignment
        """
        if db_url is None:
            db_url = cfg.read_param("template_url",
                 "Please provide the URL to connect to as template")
            if db_url is None:
                print()
                logger.error("no URL specified: aborting!")
                return -1

        if len(params) >= 1:
            db_name = ''.join(params[0])
        else:
            db_name = cfg.read_param("database_name",
                "Please provide the database to create",
                DEFAULT_DB_NAME)
        logger.debug("db_name: '%s'", db_name)

        # 1) create an object store database instance
		#    -> use it to create the database itself
        db = self.get_db(db_url, db_name)
        if db is None:
            return -1

        # check to see if the database has already been created
        if db.exists(db_name):
            logger.warn("database '{}' already exists!".format(db_name))
            return -2

	    # create the db instance
        if not db.create(db_name):
            return -1

        # create the role and assing correct access rights
        if db.dialect == "postgres":
            if len(params) == 2:
                role_name = ''.join(params[1])
            else:
                role_name = None

            if role_name is None:
                role_name = cfg.read_param("role_name",
                    "Please provide the associated role name to access the database",
                    DEFAULT_ROLE_NAME)
            logger.debug("role_name: '%s'", role_name)

            if db.exists_role(role_name) is False:
                # call function with parameter list
                params = [ role_name ]
                logger.debug("params: '%s'", params)
                if self.do_create_role(params) is False:
                    return -3

            # assign the access rights
            db.grant_db_options(role_name)

        return 0

    def create_tables(self, db_name=None, do_all_tables=False, db_url=None):
        """
        create database tables
        """
        if db_url is None:
            db_url = cfg.read_param("database_url",
                 "Please provide the URL connecting to the database")
            if db_url is None:
                logger.error("no URL specified: aborting!")
                return -1

        # 2) prepare new object store database instance
		#    use it to connect to the created database
        db = self.get_db(db_url, db_name)
        if db is None:
            return -1

        # connect to the database
        db.connect(db_name)

        # check to see if the database has already been created
        #if db.exists(db_name):
        #    logger.error("database '{}' already exists!".format(db_name))
        #    return -2

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

        # check to see what tables we shall deploy
        if cfg.read_param(None,
                "Create [a]ll tables or just the [c]urrently configured ones?",
                default="a").lower() == "a":
            print("Creating all tables ...")
            tables = [ f.replace('-create.sql', '') \
                        for f in os.listdir(schema_path) \
                        if os.path.isfile(os.path.join(schema_path, f)) and \
                            f.endswith('-create.sql') ]
        else:
            print("Creating the currently configured set of tables ...")
            if cfg.exists("database_modules"):
                tables = cfg.get("database_modules").split(" ")
            else:
                tables = STANDARD_DB_MODULES

        # check for corresponding SQL schemas files in system path
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

        # create tables from SQL schemas
        for table_file in tables_files:
            print("Running {}...".format(os.path.basename(table_file)))
            try:
                db.create_module(table_file)
            except osdbError as ex:
                logger.error("cannot import: {}".format(ex))
        logger.info("database tables have been successfully created.")

        # terminate active database connection
        db.destroy()

        return 0

    def do_create_module(self, module_name):
        """
        create database table for given module
        """

        db_url = cfg.read_param("database_url",
             "Please provide the URL to connect to the database")
        if db_url is None:
            print()
            logger.error("no URL specified: aborting!")
            return -1

        db_name = cfg.read_param("database_name",
            "Please provide the database name",
            DEFAULT_DB_NAME)
        if db_name is None:
            logger.error("no URL specified: aborting!")
            return -1

        # create an object store database instance
        db = self.get_db(db_url, db_name)
        if db is None:
            return -1

        # connect to the database
        db.connect(db_name)

        # create table from schema-file for given module name
        module = ' '.join(module_name)
        logger.debug("module_name: '%s'", module)
        #re.sub('\ |\[|\'|\]', '', module)
        #module_name.strip('[']')
        db_schema = db_url.split(":")[0]
        schema_path = self.get_schema_path(db_schema)
        if schema_path is None:
            return -1
        module_schema_file = os.path.join(schema_path,
            "{}-create.sql".format(module))
        try:
            db.create_module(module_schema_file)
            logger.info("database tables for module '%s' has been successfully created.", module_name)
        except osdbError as ex:
            logger.error("cannot import: {}".format(ex))

        # terminate active database connection
        db.destroy()

        return True

    def do_create_role(self, params=None):
        """
        create a given role (connection via URL)
        """
        db_url = cfg.read_param("template_url",
            "Please provide the URL to connect as template")

        if db_url is None:
            logger.error("no URL specified: aborting!")
            return -1

        db_template = cfg.read_param("database_template",
            "Please provide the database template name",
            DEFAULT_DB_TEMPLATE)

        if db_template is None:
            logger.error("no URL specified: aborting!")
            return -1

        # create an object store database instance
        db = self.get_db(db_url, db_template)
        if db is None:
            return -1

        if db.dialect == "postgres":
            logger.debug("params: '%s' (len: %s)", params, len(params))
            if len(params) >= 1:
                role_name = ''.join(params[0])
            else:
                role_name = None

            if role_name is None:
                role_name = cfg.read_param("role_name",
                    "Please provide the role name to create",
                    DEFAULT_ROLE_NAME)
            logger.debug("role_name: '%s'", role_name)

            if len(params) >= 2:
                role_options = ''.join(params[1])
            else:
                role_options = None

            if role_options is None:
                role_list = cfg.read_param("role_options",
                    "Please assing the list of role options to create",
                    ' '.join(DEFAULT_ROLE_OPTIONS))
                role_options = ''.join(role_list)
            logger.debug("role_options: '%s'", role_options)

            if len(params) >= 3:
                role_password = ''.join(params[2])
            else:
                role_password= 'opensipspw'
            logger.debug("role_password: '********'")

        if db.exists_role(role_name) is False:
            result =  db.create_role(role_name, role_options, role_password)
            if result:
                db.destroy()
        else:
            logger.warning("role '{}' already exists. Please use 'alter_role'".format(role_name))
            return False
        return True

    def do_drop(self, params=None):
        """
        drop a given database object (connection via URL)
        """
        db_url = self.ask_db_url()
        if db_url is None:
            return -1

        if params and len(params) > 0:
            db_name = params[0]
        else:
            db_name = cfg.read_param("database_name",
                    "Please provide the database to drop",
                    DEFAULT_DB_NAME)

        # create an object store database instance
        db = self.get_db(db_url, db_name)
        if db is None:
            return -1

        if db.dialect == "postgres":
            if params and len(params) > 1:
                role_name = params[1]
            else:
                role_name = cfg.read_param("role_name",
                    "Please provide the associated role name " +
                        "to access the database", DEFAULT_ROLE_NAME)

        # check to see if the database has already been created
        if db.exists():
            if cfg.read_param("database_force_drop",
                "Do you really want to drop the '{}' database".
                    format(db_name),
                False, True):
                if db.drop():
                    logger.info("database '%s' dropped!", db_name)
                else:
                    logger.info("database '%s' not dropped!", db_name)

                if db.dialect == "postgres":
                    if db.exists_role(role_name) is True:
                        if cfg.read_param("role_force_drop",
                            "Do you really want to drop the '{}' role".
                            format(role_name),
                            False, True):
				                # call function with parameter list
                                params = [ role_name ]
                                self.do_drop_role(params)
            else:
                logger.info("database '{}' not dropped!".format(db_name))
        else:
                logger.warning("database '{}' does not exist!".format(db_name))

    def do_drop_role(self, params=None):
        """
        drop a given role (connection to given template via URL)
        """

        db_url = cfg.read_param("template_url",
            "Please provide the URL to connect as template")

        if db_url is None:
            print()
            logger.error("no URL specified: aborting!")
            return -1

        db_template = cfg.read_param("database_template",
            "Please provide the database template name",
            DEFAULT_DB_TEMPLATE)
        if db_template is None:
            logger.error("no URL specified: aborting!")
            return -1

        # create an object store database instance
        db = self.get_db(db_url, db_template)
        if db is None:
            return -1

        role_name = None

        if len(params) >= 1:
            role_name = ''.join(params[0])

        if role_name is None:
            role_name = cfg.read_param("role_name",
                    "Please provide the role name to drop",
                    DEFAULT_ROLE_NAME)

        if db.exists_role(role_name=role_name) is True:
            if cfg.read_param("rule_force_drop",
                    "Do you really want to drop the role '{}'".
                        format(role_name),
                    False, True):
                db.drop_role(role_name)
                db.destroy()
            else:
                logger.info("role '{}' not dropped!".format(role_name))
        else:
            logger.warning("role '{}' does not exist!".format(role_name))

    def do_get_role(self, params=None):
        """
        get role attributes (connection to given template via URL)
        """

        db_url = cfg.read_param("template_url",
            "Please provide the URL to connect as template")

        if db_url is None:
            logger.error("no URL specified: aborting!")
            return -1

        db_template = cfg.read_param("database_template",
            "Please provide the database template name",
            DEFAULT_DB_TEMPLATE)
        if db_template is None:
            logger.error("no URL specified: aborting!")
            return -1

        # create an object store database instance
        db = self.get_db(db_url, db_template)
        if db is None:
            return -1

        if len(params) < 1:
            role_name = cfg.read_param("role_name",
                "Please provide the role name to alter",
                DEFAULT_ROLE_NAME)
        else:
            role_name = params[0]

        logger.debug("role_name: '%s'", role_name)


        if db.exists_role(role_name) is True:
            if db.get_role(role_name) is False:
                logger.error("get role '%s' didn't succeed", role_name)
        else:
            logger.warning("can't get options of non existing role '{}'".format(role_name))

    def do_migrate(self, params):
        if len(params) < 2:
            print("Usage: database migrate <old-database> <new-database>")
            return 0

        old_db = params[0]
        new_db = params[1]

        db_url = self.ask_db_url()
        if db_url is None:
            return -1

        # create an object store database instance
        db = self.get_db(db_url, old_db)
        if db is None:
            return -1

        if not db.exists(old_db):
             logger.error("the source database ({}) does not exist!".format(old_db))
             return -2

        print("Creating database {}...".format(new_db))
        if self._do_create_db([new_db], db_url=db_url) < 0:
            return -1
        if self.create_tables(new_db, db_url=db_url) < 0:
            return -1

        # get schema path for active database dialect
        db_schema = db.db_url.split(":")[0]
        schema_path = self.get_schema_path(db_schema)
        if schema_path is None:
            return -1

        # get schema scripts for active database dialect
        db_schema = db.db_url.split(":")[0]
        migrate_scripts = self.get_migrate_scripts_path(db_schema)
        if migrate_scripts is None:
            logger.debug("migration scripts for db_schema '%s' not found", db_schema)
            return -1
        else:
            logger.debug("migration scripts for db_schema: '%s'", migrate_scripts)

        print("Migrating all matching OpenSIPS tables...")
        db.migrate(migrate_scripts, old_db, new_db, MIGRATE_TABLES_24_TO_30)

        print("Finished copying OpenSIPS table data " +
                "into database '{}'!".format(new_db))

        db.destroy()
        return True

    def get_db(self, db_url, db_name):
        """
        helper function: check database url and its dialect
        """
        try:
            return osdb(db_url, db_name)
        except osdbArgumentError:
            logger.error("Bad URL, it should resemble: {}".format(
                "backend://user:pass@hostname" if not \
                    db_url.startswith('sqlite:') else "sqlite:///path/to/db"))
        except osdbConnectError:
            logger.error("Failed to connect to database!")
        except osdbNoSuchModuleError:
            logger.error("This database backend is not supported!  " \
                        "Supported: {}".format(', '.join(SUPPORTED_BACKENDS)))

    def get_migrate_scripts_path(self, db_schema):
        """
        helper function: migrate database schema
        """
        if self.db_path is not None:
            scripts = [
                os.path.join(self.db_path, db_schema, 'table-migrate.sql'),
                os.path.join(self.db_path, db_schema, 'db-migrate.sql'),
                ]

            if any(not os.path.isfile(i) for i in scripts):
                logger.error("The SQL migration scripts are missing!  " \
                            "Please pull the latest OpenSIPS packages!")
                return None

            return scripts

    def get_schema_path(self, db_schema):
        """
        helper function: get the path defining the root path holding sql schema template
        """
        if self.db_path is not None:
            return os.path.join(self.db_path, db_schema)

        if os.path.isfile(os.path.join('/usr/share/opensips',
                                db_schema, 'standard-create.sql')):
            self.db_path = '/usr/share/opensips'
            return os.path.join(self.db_path, db_schema)

        db_path = cfg.read_param("database_path",
                "Please provide the path to the OpenSIPS DB scripts")
        if db_path is None:
            print()
            logger.error("don't know how to find the path to the OpenSIPS DB scripts")
            return None

        if db_path.endswith('/'):
            db_path = db_path[:-1]
        if os.path.basename(db_path) == db_schema:
            db_path = os.path.dirname(db_path)

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
