#!/usr/bin/env python

from opensipscli.module import Module
from opensipscli.logger import logger
from opensipscli.config import cfg

try:
    from sqlalchemy import *
    from sqlalchemy_utils import database_exists, drop_database
    database_module = True
except ImportError:
    logger.info("cannot import database module!")
    logger.info("make sure you have sqlalchemy and sqlalchemy_utols packages installed!")
    database_module = False

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

    def __exclude__(self):
        return not database_module

    def read_param(self, param, prompt, default=None, yes_no=False):

        if cfg.exists(param):
            return cfg.get(param);
        val = ""
        if yes_no:
            prompt = prompt + " [Y/n]"
            if default is not None:
                prompt = prompt + " (Default is {})".format("Y" if default else "n")
        elif default is not None:
            prompt = prompt + " (Default value is {})".format(default)
        prompt = prompt + ": "
        while val == "":
            try:
                val = input(prompt).strip()
            except Exception as e:
                return None
            if val == "":
                if default is not None:
                    return default
            elif yes_no:
                if val.lower() in ['y', 'yes']:
                    return True
                elif val.lower() in ['n', 'no']:
                    return False
                else:
                    prompt = "Please choose 'Y' or 'n': "
            else:
                return val

    def get_schema_path(self, db_schema):
        db_path = self.read_param("database_path",
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
        return schema_path

    def do_drop(self, params=None):

        db_url = self.read_param("database_url",
                "Please provide us the URL of the database")
        if db_url is None:
            print()
            logger.error("no URL specified: aborting!")
            return -1

        if params and len(params) > 1:
            db_name = params[0]
        else:
            db_name = self.read_param("database_name",
                    "Please provide the database to drop",
                    DEFAULT_DB_NAME)
        # check to see if the database has already been created
        try:
            database_url = "{}/{}".format(db_url, db_name)
            if database_exists(database_url):
                if self.read_param("database_force_drop",
                        "Do you really want to drop the '{}' database".
                            format(db_name),
                        False, True):
                    drop_database(database_url)
            else:
                logger.warning("database '{}' does not exist!".format(db_name))
        except ModuleNotFoundError as me:
            logger.error("cannot check if database {} exists: {}".
                    format(db_name, me))
            return -1

    def do_add(self, params):

        if len(params) < 1:
            logger.error("No module added")
            return -1
        module = params[0]

        if len(params) < 2:
            db_name = self.read_param("database_name",
                    "Please provide the database to drop",
                    DEFAULT_DB_NAME)
        else:
            db_name = params[1]

        db_url = self.read_param("database_url",
                "Please provide us the URL of the database")
        if db_url is None:
            print()
            logger.error("no URL specified: aborting!")
            return -1

        # check to see if the database exists
        try:
            database_url = "{}/{}".format(db_url, db_name)
            if not database_exists(database_url):
                logger.warning("database '{}' does not exist!".format(db_name))
                return -1
        except ModuleNotFoundError as me:
            logger.error("cannot check if database {} exists: {}".
                    format(db_name, me))
            return -1

        db_schema = db_url.split(":")[0]
        schema_path = self.get_schema_path(db_schema)
        if schema_path is None:
            return -1

        module_file_path = os.path.join(schema_path,
                "{}-create.sql".format(module))
        if not os.path.isfile(module_file_path):
            logger.warning("cannot find OpenSIPS DB file: '{}'!".
                    format(module_file_path))
            return -1

        conn = create_engine(database_url).connect()
        with open(module_file_path, 'r') as f:
            try:
                conn.execute(f.read())
            except Exception as e:
                logger.error("cannot add module {}: {}".
                        format(module, e))
                return -2

        conn.close()
        logger.info("Module {} has been successfully added!".
                format(module))
        return 0

    def do_create(self, params=None):

        db_url = self.read_param("database_url",
                "Please provide us the URL of the database")
        if db_url is None:
            print()
            logger.error("no URL specified: aborting!")
            return -1
        if params and len(params) > 1:
            db_name = params[0]
        else:
            db_name = self.read_param("database_name",
                    "Please provide the database to create",
                    DEFAULT_DB_NAME)
        # check to see if the database has already been created
        try:
            database_url = "{}/{}".format(db_url, db_name)
            if database_exists(database_url):
                logger.warn("database '{}' already exists!".format(db_name))
                return -2
        except ModuleNotFoundError as me:
            logger.error("cannot check if database {} exists: {}".
                    format(db_name, me))
            return -1
        db_schema = db_url.split(":")[0]
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

        engine = create_engine(db_url)
        conn = engine.connect()

        # all good - it's time to create the database
        conn.execute("CREATE DATABASE {}".format(db_name))
        conn.execute("USE {}".format(db_name))

        for table_file in tables_files:
            with open(table_file, 'r') as f:
                conn.execute(f.read())

        conn.close()
        logger.info("The database has been successfully created.")
        return 0
