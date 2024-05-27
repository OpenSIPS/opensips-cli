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
    SUPPORTED_BACKENDS,
)

import os, re
from getpass import getpass, getuser
from collections import OrderedDict

DEFAULT_DB_TEMPLATE = "template1"
OPENSIPS_SCHEMA_SRC_PATH = "/usr/local/share/opensips"

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
    "domainpolicy",
    "emergency",
    "fraud_detection",
    "freeswitch_scripting",
    "imc",
    "presence",
    "registrant",
    "rls",
    "smpp",
    "tracer",
    "userblacklist"
]

DB_MIGRATIONS = {
    '3.3_to_3.4': [
        'dispatcher',        # changed in 3.4
        'cc_agents',
        'acc',
        'active_watchers',
        'address',
        'b2b_entities',
        'b2b_logic',
        'b2b_sca',
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
        'dialog',
        'dialplan',
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
        'jwt_profiles',
        'jwt_secrets',
        'load_balancer',
        'location',
        'missed_calls',
        'presentity',
        'pua',
        'qr_profiles',
        'rc_clients',
        'rc_demo_ratesheet',
        'rc_ratesheets',
        'rc_vendors',
        're_grp',
        'registrant',
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
        'tcp_mgm',
        'tls_mgm',
        'uri',
        'userblacklist',
        'usr_preferences',
        'watchers',
        'xcap',
    ],

    '3.2_to_3.3': [
        'cc_agents',         # changed in 3.3
        'cc_calls'           # changed in 3.3
        'cc_cdrs',           # changed in 3.3
        'tcp_mgm',           # new in 3.3
        'acc',
        'active_watchers',
        'address',
        'b2b_entities',
        'b2b_logic',
        'b2b_sca',
        'cachedb',
        'carrierfailureroute',
        'carrierroute',
        'cc_flows',
        'closeddial',
        'clusterer',
        'cpl',
        'dbaliases',
        'dialog',
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
        'jwt_profiles',
        'jwt_secrets',
        'load_balancer',
        'location',
        'missed_calls',
        'presentity',
        'pua',
        'qr_profiles',
        'rc_clients',
        'rc_demo_ratesheet',
        'rc_ratesheets',
        'rc_vendors',
        're_grp',
        'registrant',
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
        'tls_mgm',
        'uri',
        'userblacklist',
        'usr_preferences',
        'watchers',
        'xcap',
    ],

    '3.1_to_3.2': [
        'b2b_logic',         # changed in 3.2
        'pua',               # changed in 3.2
        'registrant',        # changed in 3.2
        'subscriber',        # changed in 3.2
        'jwt_profiles',      # new in 3.1
        'jwt_secrets',       # new in 3.1
        'qr_profiles',       # new in 3.1
        'rc_clients',        # new in 3.1
        'rc_vendors',        # new in 3.1
        'rc_ratesheets',     # new in 3.1
        'rc_demo_ratesheet', # new in 3.1
        'acc',
        'active_watchers',
        'address',
        'b2b_entities',
        'b2b_sca',
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
        'dialog',
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
        'tls_mgm',
        'uri',
        'userblacklist',
        'usr_preferences',
        'watchers',
        'xcap',
    ],

    '3.0_to_3.1': [
        'smpp',          # new in 3.0
        'cc_agents',     # changed in 3.1
        'cc_calls',      # changed in 3.1
        'cc_flows',      # changed in 3.1
        'dialog',        # changed in 3.1
        'dr_carriers',   # changed in 3.1
        'dr_rules',      # changed in 3.1
        'load_balancer', # changed in 3.1
        'acc',
        'active_watchers',
        'address',
        'b2b_entities',
        'b2b_logic',
        'b2b_sca',
        'cachedb',
        'carrierfailureroute',
        'carrierroute',
        'cc_cdrs',
        'closeddial',
        'clusterer',
        'cpl',
        'dbaliases',
        'dialplan',
        'dispatcher',
        'domain',
        'domainpolicy',
        'dr_gateways',
        'dr_groups',
        'dr_partitions',
        'emergency_report',
        'emergency_routing',
        'emergency_service_provider',
        'fraud_detection',
        'freeswitch',
        'globalblacklist',
        'grp',
        'imc_members',
        'imc_rooms',
        'location',
        'missed_calls',
        'presentity',
        'pua',
        're_grp',
        'registrant',
        'rls_presentity',
        'rls_watchers',
        'route_tree',
        'rtpengine',
        'rtpproxy_sockets',
        'silo',
        'sip_trace',
        'speed_dial',
        'subscriber',
        'tls_mgm',
        'uri',
        'userblacklist',
        'usr_preferences',
        'watchers',
        'xcap',
    ],

    '2.4_to_3.0': [
        'registrant', # changed in 3.0
        'tls_mgm',    # changed in 3.0
        'acc',
        'active_watchers',
        'address',
        'b2b_entities',
        'b2b_logic',
        'b2b_sca',
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
        'dialog',
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
        'speed_dial',
        'subscriber',
        'uri',
        'userblacklist',
        'usr_preferences',
        'watchers',
        'xcap',
    ],
}


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
            arg = len(line.split())
            if arg == 2 or (arg == 3 and line[-1] != ' '):
                mig_flavours = [f + ' ' for f in DB_MIGRATIONS]
                if not text:
                    return mig_flavours
                ret = [t for t in mig_flavours if t.startswith(text)]

            elif arg == 3 or (arg == 4 and line[-1] != ' '):
                db_source = ['opensips ']
                if not text:
                    return db_source
                ret = [t for t in db_source if t.startswith(text)]

            elif arg == 4 or (arg == 5 and line[-1] != ' '):
                db_dest = ['opensips_new ']
                if not text:
                    return db_dest
                ret = [t for t in db_dest if t.startswith(text)]

        return ret or ['']

    def __exclude__(self):
        """
        method exlusion list
        """
        if cfg.exists("database_url"):
            db_url = cfg.get("database_url")
            return (not osdb.has_dialect(osdb.get_dialect(db_url)), None)
        else:
            return (not osdb.has_sqlalchemy(), None)

    def __get_methods__(self):
        """
        methods available for autocompletion
        """
        return [
            'create',
            'drop',
            'add',
            'migrate',
            ]

    def get_db_url(self, db_name=cfg.get('database_name')):
        engine = osdb.get_db_engine()
        if not engine:
            return None

        # make sure to inherit the 'database_admin_url' engine + host
        db_url = osdb.set_url_driver(cfg.get("database_url"), engine)
        db_url = osdb.set_url_host(db_url, osdb.get_db_host())

        logger.debug("DB URL: '{}'".format(db_url))
        return db_url

    def get_admin_db_url(self, db_name):
        engine = osdb.get_db_engine()
        if not engine:
            return None

        if cfg.exists('database_admin_url'):
            admin_url = cfg.get("database_admin_url")
            if engine == "postgresql":
                admin_url = osdb.set_url_db(admin_url, 'postgres')
            else:
                admin_url = osdb.set_url_db(admin_url, None)
        else:
            if engine == 'postgresql':
                if getuser() != "postgres":
                    logger.error("Command must be run as 'postgres' user: "
                                 "sudo -u postgres opensips-cli ...")
                    return None

                """
                For PG, do the initial setup using 'postgres' as role + DB
                """
                admin_url = "postgresql://postgres@localhost/postgres"
            else:
                admin_url = "{}://root@localhost".format(engine)

        if osdb.get_url_pswd(admin_url) is None:
            pswd = getpass("Password for admin {} user ({}): ".format(
                osdb.get_url_driver(admin_url, capitalize=True),
                osdb.get_url_user(admin_url)))
            logger.debug("read password: '%s'", pswd)
            admin_url = osdb.set_url_password(admin_url, pswd)

        logger.debug("admin DB URL: '{}'".format(admin_url))
        return admin_url

    def do_add(self, params, modifiers=None):
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

        engine = osdb.get_db_engine()
        if not engine:
            return -1

        if engine != 'sqlite':
            admin_url = self.get_admin_db_url(db_name)
            if not admin_url:
                return -1

        db = self.get_db(admin_url if engine != 'sqlite' else db_url, db_name)
        if not db:
            return -1

        if engine == 'sqlite' and not db.exists(db_name):
            logger.error("database '%s' does not exist!", db_name)
            return -1

        ret = self.create_tables(db_name, db_url, db, tables=[module],
                                 create_std=False)

        db.destroy()
        return ret


    def do_create(self, params=None, modifiers=None):
        """
        create database with role-assigment and tables
        """
        if len(params) >= 1:
            db_name = params[0]
        else:
            db_name = cfg.read_param("database_name",
                "Please provide the database to create")
        logger.debug("db_name: '%s'", db_name)

        engine = osdb.get_db_engine()
        if not engine:
            return -1

        if engine != 'sqlite':
            admin_url = self.get_admin_db_url(db_name)
            if not admin_url:
                return -1

        db_url = self.get_db_url(db_name)
        if not db_url:
            return -1

        db = self.get_db(admin_url if engine != 'sqlite' else db_url, db_name)
        if not db:
            return -1

        if self.create_db(db_name, \
            admin_url if engine != 'sqlite' else db_url, db) < 0:
            return -1

        if self.ensure_user(db_url, db_name, db) < 0:
            return -1

        if self.create_tables(db_name, db_url, db) < 0:
            return -1

        db.destroy()
        return 0

    def create_db(self, db_name, admin_url, db=None):
        # 1) create an object store database instance
        #    -> use it to create the database itself
        if not db:
            db = self.get_db(admin_url, db_name)
            if not db:
                return -1
            destroy = True
        else:
            destroy = False

        # check to see if the database has already been created
        if db.exists(db_name):
            logger.warn("database '%s' already exists!", db_name)
            return -2

        # create the db instance
        if not db.create(db_name):
            return -1

        if destroy:
            db.destroy()
        return 0

    def create_tables(self, db_name, db_url, admin_db, tables=[],
                        create_std=True):
        """
        create database tables
        """
        if admin_db.dialect != "sqlite":
            db_url = osdb.set_url_db(db_url, db_name)
        else:
            db_url = 'sqlite:///' + db_name

        # 2) prepare new object store database instance
        #    use it to connect to the created database
        db = self.get_db(db_url, db_name)
        if db is None:
            return -1

        if admin_db.dialect != "sqlite" and not db.exists():
            logger.warning("database '{}' does not exist!".format(db_name))
            return -1

        schema_path = self.get_schema_path(db.dialect)
        if schema_path is None:
            return -1

        table_files = OrderedDict()

        if create_std:
            standard_file_path = os.path.join(schema_path, "standard-create.sql")
            if not os.path.isfile(standard_file_path):
                logger.error("cannot find stardard OpenSIPS DB file: '{}'!".
                        format(standard_file_path))
                return -1
            table_files['standard'] = standard_file_path

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

        username = osdb.get_url_user(db_url)
        admin_db.connect(db_name)

        if db.dialect == "postgresql":
            self.pg_grant_schema(username, admin_db)

        # create tables from SQL schemas
        for module, table_file in table_files.items():
            logger.info("Running {}...".format(os.path.basename(table_file)))
            try:
                db.create_module(table_file)
                if db.dialect == "postgresql":
                    self.pg_grant_table_access(table_file, username, admin_db)
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
        if admin_db.dialect != "sqlite":
            db_url = osdb.set_url_db(db_url, db_name)
        else:
            db_url = 'sqlite:///' + db_name

        try:
            db = self.get_db(db_url, db_name, check_access=True)
            logger.info("connected to DB, '%s' user is already created",
                        osdb.get_url_user(db_url))
        except osdbAccessDeniedError:
            logger.info("creating access user for {} ...".format(db_name))
            if not admin_db.ensure_user(db_url):
                logger.error("failed to create user on {} DB".format(db_name))
                return -1

            db = self.get_db(db_url, db_name, cfg_url_param='database_url')
            if db is None:
                return -1

        db.destroy()
        return 0

    def do_drop(self, params=None, modifiers=None):
        """
        drop a given database object (connection via URL)
        For PostgreSQL, perform this operation using 'postgres' as role + DB
        """
        if params and len(params) > 0:
            db_name = params[0]
        else:
            db_name = cfg.read_param("database_name",
                    "Please provide the database to drop")

        engine = osdb.get_db_engine()
        if not engine:
            return -1

        if engine != 'sqlite':
            db_url = self.get_admin_db_url(db_name)
            if db_url is None:
                return -1

            if db_url.lower().startswith("postgresql"):
                db_url = osdb.set_url_db(db_url, 'postgres')
        else:
            db_url = self.get_db_url(db_name)
            if not db_url:
                return -1

        # create an object store database instance
        db = self.get_db(db_url, db_name)
        if db is None:
            return -1

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
            db.destroy()
            return -1

        db.destroy()
        return 0


    def do_migrate(self, params, modifiers=None):
        if len(params) < 3:
            print("Usage: database migrate <flavour> <old-database> <new-database>")
            return 0

        flavour = params[0].lower()
        old_db = params[1]
        new_db = params[2]

        if flavour not in DB_MIGRATIONS:
            logger.error("unsupported migration flavour: {}".format(flavour))
            return -1

        admin_url = self.get_admin_db_url(new_db)
        if not admin_url:
            return -1

        db = self.get_db(admin_url, new_db)
        if not db:
            return -1

        if db.dialect != "mysql":
            logger.error("'migrate' is only available for MySQL right now! :(")
            return -1

        if not db.exists(old_db):
             logger.error("the source database ({}) does not exist!".format(old_db))
             return -2

        print("Creating database {}...".format(new_db))
        if self.create_db(new_db, admin_url, db) < 0:
            return -1
        if self.create_tables(new_db, admin_url, db) < 0:
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
            logger.debug("found migration scripts for %s", backend)

        logger.info("Migrating all matching OpenSIPS tables...")
        db.migrate(flavour.replace('.', '_').upper(),
                    migrate_scripts, old_db, new_db, DB_MIGRATIONS[flavour])

        db.destroy()
        return True

    def get_db(self, db_url, db_name, cfg_url_param="database_admin_url",
                check_access=False):
        """
        helper function: check database url and its dialect
        """
        try:
            return osdb(db_url, db_name)
        except osdbAccessDeniedError:
            if check_access:
                raise
            logger.error("failed to connect to DB as %s, please provide or " +
                "fix the '%s'", osdb.get_url_user(db_url), cfg_url_param)
        except osdbArgumentError:
            logger.error("Bad URL, it should resemble: {}".format(
                "backend://user:pass@hostname" if not \
                    db_url.startswith('sqlite:') else "sqlite:////path/to/db"))
        except osdbConnectError:
            logger.error("Failed to connect to database!")
        except osdbNoSuchModuleError:
            logger.error("This database backend is not supported!  " \
                        "Supported: {}".format(', '.join(SUPPORTED_BACKENDS)))

    def get_migrate_scripts_path(self, backend="mysql"):
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

            for s in scripts:
                if not os.path.isfile(s):
                    logger.error("Missing migration script ({}), please pull" \
                            " the latest OpenSIPS {} module package!".format(
                                s, backend))
                    return None

            return scripts

    def get_schema_path(self, backend="mysql"):
        """
        helper function: get the path defining the root path holding sql schema template
        """
        if '+' in backend:
            backend = backend[0:backend.index('+')]

        if self.db_path is not None:
            return os.path.join(self.db_path, backend)

        db_path = os.path.expanduser(cfg.get("database_schema_path"))

        if db_path.endswith('/'):
            db_path = db_path[:-1]
        if os.path.basename(db_path) == backend:
            db_path = os.path.dirname(db_path)

        if not os.path.exists(db_path):
            if not os.path.exists(OPENSIPS_SCHEMA_SRC_PATH):
                logger.error("path '{}' to OpenSIPS DB scripts does not exist!".
                        format(db_path))
                return None

            logger.info("schema path '{}' not found, using '{}' instead (detected on system)".
                    format(db_path, OPENSIPS_SCHEMA_SRC_PATH))
            db_path = OPENSIPS_SCHEMA_SRC_PATH

        if not os.path.isdir(db_path):
            logger.error("path '{}' to OpenSIPS DB scripts is not a directory!".
                    format(db_path))
            return None
        
        def build_schema_path(db_path, backend):
            """
            Replaces schema path of postgresql to old postgre schema path if exists.
            Should be deleted after opensips main repo refactors folder name to the new backend name.
            """
            if backend == "postgresql":
                old_postgre_path = os.path.join(db_path, "postgres")
                if os.path.isdir(old_postgre_path):
                    return old_postgre_path
            schema_path = os.path.join(db_path, backend)
            return schema_path
        
        schema_path = build_schema_path(db_path, backend)
        if not os.path.isdir(schema_path):
            logger.error("invalid OpenSIPS DB scripts dir: '{}'!".
                    format(schema_path))
            return None

        std_tables = os.path.join(schema_path, 'standard-create.sql')
        if not os.path.isfile(std_tables):
            logger.error("standard tables file not found ({})".format(std_tables))
            return None

        self.db_path = db_path
        return schema_path

    def pg_grant_table_access(self, sql_file, username, admin_db):
        """
        Grant access to all tables and sequence IDs of a DB module
        """
        with open(sql_file, "r") as f:
            for line in f.readlines():
                res = re.search('CREATE TABLE (.*) ', line, re.IGNORECASE)
                if res:
                    table = res.group(1)
                    admin_db.grant_table_options(username, table)

                res = re.search('ALTER SEQUENCE (.*) MAXVALUE', line,
                                re.IGNORECASE)
                if res:
                    seq = res.group(1)
                    admin_db.grant_table_options(username, seq)
                    
    def pg_grant_schema(self, username, admin_db):
        """
        Grant access to public schema of DB
        """
        admin_db.grant_public_schema(username)
