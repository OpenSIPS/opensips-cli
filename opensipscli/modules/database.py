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
    osdbArgumentError, osdbNoSuchModuleError,
    osdbModuleAlreadyExistsError, osdbAccessDeniedError,
)

import os
from getpass import getpass, getuser

DEFAULT_DB_TEMPLATE = "template1"

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
        elif command == 'add':
            modules = STANDARD_DB_MODULES + EXTRA_DB_MODULES
            if not text:
                return modules

            ret = [t for t in modules if t.startswith(text)]
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

        return ret or ['']

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
        return [
            'create',
            'drop',
            'add',
            'migrate',
            'create_role',
            'alter_role',
            'drop_role',
            'get_role',
            ]

    def get_db_engine(self):
        if cfg.exists('database_admin_url'):
            engine = osdb.get_url_driver(cfg.get('database_admin_url'))
        elif cfg.exists('database_url'):
            engine = osdb.get_url_driver(cfg.get('database_url'))
        else:
            engine = "mysql"

        if engine not in SUPPORTED_BACKENDS:
            logger.error("bad database engine ({}), supported: {}".format(
                         engine, " ".join(SUPPORTED_BACKENDS)))
            return None
        return engine

    def get_db_url(self, db_name=cfg.get('database_name')):
        engine = self.get_db_engine()
        if not engine:
            return None

        # make sure to inherit the 'database_admin_url' engine
        db_url = osdb.set_url_driver(cfg.get("database_url"), engine)

        logger.debug("DB URL: '{}'".format(db_url))
        return db_url

    def get_admin_db_url(self, db_name):
        engine = self.get_db_engine()
        if not engine:
            return None

        if cfg.exists('database_admin_url'):
            admin_url = cfg.get("database_admin_url")
            if engine == "postgres":
                admin_url = osdb.set_url_db(admin_url, 'postgres')
        else:
            if engine == 'postgres':
                if getuser() != "postgres":
                    logger.error("Command must be run as 'postgres' user: "
                                 "sudo -u postgres opensips-cli ...")
                    return None

                """
                For PG, do the initial setup using 'postgres' as role + DB
                """
                admin_url = "postgres://postgres@localhost/postgres"
            else:
                admin_url = "{}://root@localhost".format(engine)

        logger.debug("admin DB URL: '{}'".format(admin_url))
        return admin_url

    def do_add(self, params):
        """
        add a given table to the database (connection via URL)
        """
        if len(params) < 1:
            logger.error("Please specify a module to add (e.g. dialog)")
            return -1
        module = params[0]

        if len(params) < 2:
            db_name = cfg.read_param("database_name",
                    "Please provide the database to add the module to")
        else:
            db_name = params[1]

        db_url = self.get_db_url(db_name)
        if not db_url:
            logger.error("no DB URL specified: aborting!")
            return -1

        return self.create_tables(db_name, db_url, tables=[module],
                                    create_std=False)

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
                "Please provide the role name to alter")
            logger.debug("role_name: '%s'", role_name)

        if db.exists_role(role_name) is True:
            if len(params) > 1:
                role_options = params[1]
            if len(params) > 2:
                role_password = params[2]

            if role_options is None:
                role_list = cfg.read_param("role_options",
                    "Please adapt the role options to alter")
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
            db_name = params[0]
        else:
            db_name = cfg.read_param("database_name",
                "Please provide the database to create")
        logger.debug("db_name: '%s'", db_name)

        admin_url = self.get_admin_db_url(db_name)
        if not admin_url:
            return -1

        try:
            admin_db = self.get_db(admin_url, db_name)
        except osdbAccessDeniedError:
            logger.error("failed to connect to DB as root, check " +
                            "'database_admin_url'")
            return -1
        if not admin_db:
            return -1

        if self.create_db(db_name, admin_url, admin_db) < 0:
            return -1

        db_url = self.get_db_url(db_name)
        if not db_url:
            return -1

        if self.ensure_user(db_url, db_name, admin_db) < 0:
            return -1

        if self.create_tables(db_name, db_url) < 0:
            return -1

        return 0

    def create_db(self, db_name, admin_url, db=None):
        # 1) create an object store database instance
        #    -> use it to create the database itself
        if not db:
            db = self.get_db(admin_url, db_name)
            if not db:
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
            role_name = cfg.read_param("role_name",
                "Please provide a role name to access the database")
            logger.debug("role_name: '%s'", role_name)

            if db.exists_role(role_name) is False:
                if self.do_create_role([role_name]) is False:
                    return -3

            # assign the access rights
            db.grant_db_options(role_name)

        return 0

    def create_tables(self, db_name, db_url, tables=[], create_std=True):
        """
        create database tables
        """

        # 2) prepare new object store database instance
        #    use it to connect to the created database
        db = self.get_db(db_url, db_name)
        if db is None:
            return -1

        if not db.exists():
            logger.warning("database '{}' does not exist!".format(db_name))
            return -1

        # connect to the database
        db.connect(db_name)

        schema_path = self.get_schema_path(db.dialect)
        if schema_path is None:
            return -1

        if create_std:
            standard_file_path = os.path.join(schema_path, "standard-create.sql")
            if not os.path.isfile(standard_file_path):
                logger.error("cannot find stardard OpenSIPS DB file: '{}'!".
                        format(standard_file_path))
                return -1
            table_files = {'standard': standard_file_path}
        else:
            table_files = {}

        # check to see what tables we shall deploy
        if tables:
            pass
        elif cfg.exists("database_modules"):
            # we know exactly what modules we want to instsall
            tables_line = cfg.get("database_modules").strip().lower()
            if tables_line == "all":
                logger.debug("Creating all tables")
                tables = [ f.replace('-create.sql', '') \
                            for f in os.listdir(schema_path) \
                            if os.path.isfile(os.path.join(schema_path, f)) and \
                                f.endswith('-create.sql') ]
            else:
                logger.debug("Creating custom tables")
                tables = tables_line.split(" ")
        else:
            logger.debug("Creating standard tables")
            tables = STANDARD_DB_MODULES

        # check for corresponding SQL schemas files in system path
        logger.debug("checking tables: {}".format(" ".join(tables)))

        for table in tables:
            if table == "standard":
                # already checked for it
                continue
            table_file_path = os.path.join(schema_path,
                    "{}-create.sql".format(table))
            if not os.path.isfile(table_file_path):
                logger.warn("cannot find SQL file for module {}: {}".
                        format(table, table_file_path))
            else:
                table_files[table] = table_file_path

        # create tables from SQL schemas
        for module, table_file in table_files.items():
            print("Running {}...".format(os.path.basename(table_file)))
            try:
                db.create_module(table_file)
                logger.info("database table(s) have been successfully created")
            except osdbModuleAlreadyExistsError:
                logger.error("{} table(s) are already created!".format(module))
            except osdbError as ex:
                logger.error("cannot import: {}".format(ex))

        # terminate active database connection
        db.destroy()
        return 0

    def ensure_user(self, db_url, db_name, admin_db):
        """
        Ensures that the user/password in @db_url can connect to @db_name.
        It assumes @db_name has been created beforehand.  If the user doesn't
        exist or has insufficient permissions, this will be fixed using the
        @admin_db connection.
        """
        db_url = osdb.set_url_db(db_url, db_name)

        try:
            db = self.get_db(db_url, db_name)
            logger.info("access works, opensips user already exists")
        except osdbAccessDeniedError:
            logger.info("creating access user for {} ...".format(db_name))
            if not admin_db.create_user(db_url, db_name):
                logger.error("failed to create user on {} DB".format(db_name))
                return -1

            try:
                db = self.get_db(db_url, db_name)
            except Exception as e:
                logger.exception(e)
                logger.error("failed to connect to {} " +
                                "with non-admin user".format(db_name))
                return -1

        db.destroy()
        return 0

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
                    "Please provide the role name to create")
            logger.debug("role_name: '%s'", role_name)

            if len(params) >= 2:
                role_options = ''.join(params[1])
            else:
                role_options = None

            if role_options is None:
                role_list = cfg.read_param("role_options",
                    "Please assing the list of role options to create")
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
        For PostgreSQL, perform this operation using 'postgres' as role + DB
        """
        if params and len(params) > 0:
            db_name = params[0]
        else:
            db_name = cfg.read_param("database_name",
                    "Please provide the database to drop")

        admin_db_url = self.get_admin_db_url(db_name)
        if admin_db_url is None:
            return -1

        if admin_db_url.lower().startswith("postgres"):
            admin_db_url = osdb.set_url_db(admin_db_url, 'postgres')

        # create an object store database instance
        db = self.get_db(admin_db_url, db_name)
        if db is None:
            return -1

        if db.dialect == "postgres":
            if params and len(params) > 1:
                role_name = params[1]
            else:
                role_name = cfg.read_param("role_name",
                    "Please provide a role name to access the database")

        # check to see if the database has already been created
        if db.exists():
            if cfg.read_param("database_force_drop",
                "Do you really want to drop the '{}' database".
                    format(db_name),
                False, True, isbool=True):

                if db.drop():
                    logger.info("database '%s' dropped!", db_name)
                else:
                    logger.info("database '%s' not dropped!", db_name)
            else:
                logger.info("database '{}' not dropped!".format(db_name))
        else:
            logger.warning("database '{}' does not exist!".format(db_name))
            return -1

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
                    "Please provide the role name to drop")

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
                "Please provide the role name to alter")
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

        admin_url = self.get_admin_db_url(new_db)
        if not admin_url:
            return -1

        try:
            db = self.get_db(admin_url, new_db)
        except osdbAccessDeniedError:
            logger.error("failed to connect to DB as root, check " +
                            "'database_admin_url'")
            return -1
        if not db:
            return -1

        if not db.exists(old_db):
             logger.error("the source database ({}) does not exist!".format(old_db))
             return -2

        print("Creating database {}...".format(new_db))
        if self.create_db(new_db, admin_url, db) < 0:
            return -1
        if self.create_tables(new_db, admin_url) < 0:
            return -1

        backend = osdb.get_url_driver(admin_url)

        # obtain the DB schema files for the in-use backend
        schema_path = self.get_schema_path(backend)
        if schema_path is None:
            return -1

        migrate_scripts = self.get_migrate_scripts_path(backend)
        if migrate_scripts is None:
            logger.debug("migration scripts for %s not found", backend)
            return -1
        else:
            logger.debug("migration scripts for %s", migrate_scripts)

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

    def get_migrate_scripts_path(self, backend):
        """
        helper function: migrate database schema
        """
        if '+' in backend:
            backend = backend[0:backend.index('+')]

        if self.db_path is not None:
            scripts = [
                os.path.join(self.db_path, backend, 'table-migrate.sql'),
                os.path.join(self.db_path, backend, 'db-migrate.sql'),
                ]

            if any(not os.path.isfile(i) for i in scripts):
                logger.error("The SQL migration scripts are missing!  " \
                            "Please pull the latest OpenSIPS packages!")
                return None

            return scripts

    def get_schema_path(self, backend):
        """
        helper function: get the path defining the root path holding sql schema template
        """
        if '+' in backend:
            backend = backend[0:backend.index('+')]

        if self.db_path is not None:
            return os.path.join(self.db_path, backend)

        if os.path.isfile(os.path.join('/usr/share/opensips',
                                backend, 'standard-create.sql')):
            self.db_path = '/usr/share/opensips'
            return os.path.join(self.db_path, backend)

        db_path = cfg.read_param("database_path",
                "Could not locate DB schema files for {}!  Custom path".format(
                    backend))
        if db_path is None:
            print()
            logger.error("failed to locate {} DB schema files".format(backend))
            return None

        if db_path.endswith('/'):
            db_path = db_path[:-1]
        if os.path.basename(db_path) == backend:
            db_path = os.path.dirname(db_path)

        if not os.path.exists(db_path):
            logger.error("path '{}' to OpenSIPS DB scripts does not exist!".
                    format(db_path))
            return None
        if not os.path.isdir(db_path):
            logger.error("path '{}' to OpenSIPS DB scripts is not a directory!".
                    format(db_path))
            return None

        schema_path = os.path.join(db_path, backend)
        if not os.path.isdir(schema_path):
            logger.error("invalid OpenSIPS DB scripts dir: '{}'!".
                    format(schema_path))
            return None

        self.db_path = db_path
        return schema_path
