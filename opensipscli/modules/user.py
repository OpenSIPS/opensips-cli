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
        osdb, osdbError
)

import os
import getpass
import hashlib

DEFAULT_DB_NAME = "opensips"
USER_TABLE = "subscriber"
USER_NAME_COL = "username"
USER_DOMAIN_COL = "domain"
USER_PASS_COL = "password"
USER_HA1_COL = "ha1"
USER_HA1B_COL = "ha1b"
USER_HA1_SHA256_COL = "ha1_sha256"
USER_HA1_SHA512T256_COL = "ha1_sha512t256"
USER_RPID_COL = "rpid"

class user(Module):

    def user_db_connect(self):
        engine = osdb.get_db_engine()

        db_url = cfg.read_param(["database_user_url", "database_url"],
                "Please provide us the URL of the database")
        if db_url is None:
            print()
            logger.error("no URL specified: aborting!")
            return None, None

        db_url = osdb.set_url_driver(db_url, engine)
        db_name = cfg.read_param(["database_user_name", "database_name"],
                "Please provide the database to add user to", DEFAULT_DB_NAME)

        try:
            db = osdb(db_url, db_name)
        except osdbError:
            logger.error("failed to connect to database %s", db_name)
            return None, None

        if not db.connect():
            return None, None

        res = db.find('version', 'table_version', {'table_name': USER_TABLE})
        if not res:
            osips_ver = '3.2+'
        else:
            # RFC 8760 support was introduced in OpenSIPS 3.2 (table ver 8+)
            tb_ver = res.first()[0]
            if tb_ver >= 8:
                osips_ver = '3.2+'
            else:
                osips_ver = '3.1'

        return db, osips_ver

    def user_get_domain(self, name):
        s = name.split('@')
        if len(s) > 2:
            logger.warning("invalid username {}".
                    format(name))
            return None
        elif len(s) == 1:
            domain = cfg.read_param("domain",
                    "Please provide the domain of the user")
            if not domain:
                logger.warning("no domain specified for {}".
                        format(name))
                return None
            return name, domain
        return s[0], s[1]

    def user_get_password(self):
        while True:
            pw1 = getpass.getpass("Please enter new password: ")
            pw2 = getpass.getpass("Please repeat the password: ")
            if pw1 != pw2:
                logger.warning("passwords are not the same! Please retry...")
            else:
                return pw1

    def user_get_ha1(self, user, domain, password):
        string = "{}:{}:{}".format(user, domain, password)
        return hashlib.md5(string.encode('utf-8')).hexdigest()

    def user_get_ha1b(self, user, domain, password):
        string = "{}@{}:{}:{}".format(user, domain, domain, password)
        return hashlib.md5(string.encode('utf-8')).hexdigest()

    def user_get_ha1_sha256(self, user, domain, password):
        string = "{}:{}:{}".format(user, domain, password)
        return hashlib.sha256(string.encode('utf-8')).hexdigest()

    def user_get_ha1_sha512t256(self, user, domain, password):
        string = "{}:{}:{}".format(user, domain, password)
        try:
            o = hashlib.new("sha512-256")
        except ValueError:
            # SHA-512/256 is only available w/ OpenSSL 1.1.1 (Sep 2018) or
            # newer, so let's just leave the field blank if we get an exception
            logger.error(("The SHA-512/256 hashing algorithm is "
                            "apparently not available!?"))
            logger.error("Adding user, but with a blank '{}' column!".format(
                    USER_HA1_SHA512T256_COL))
            logger.error("Tip: installing OpenSSL 1.1.1+ should fix this")
            return ""

        o.update(string.encode('utf-8'))
        return o.hexdigest()

    def do_add(self, params=None, modifiers=None):

        if len(params) < 1:
            name = cfg.read_param(None,
                    "Please provide the username you want to add")
            if not name:
                logger.warning("no username to add!")
                return -1
        else:
            name = params[0]
        username, domain = self.user_get_domain(name)

        db, osips_ver = self.user_db_connect()
        if not db:
            return -1

        insert_dict = {
                USER_NAME_COL: username,
                USER_DOMAIN_COL: domain
            }
        # check if the user already exists
        if db.entry_exists(USER_TABLE, insert_dict):
            logger.error("User {}@{} already exists".
                    format(username, domain))
            return -1

        if len(params) > 1:
            password = params[1]
        else:
            password = self.user_get_password()
            if password is None:
                logger.error("password not specified: cannot add user {}@{}".
                        format(user, domain))
                return -1
        insert_dict[USER_HA1_COL] = \
                self.user_get_ha1(username, domain, password)

        # only populate the 'ha1b' column on 3.1 or older OpenSIPS DBs
        if osips_ver < '3.2':
            insert_dict[USER_HA1B_COL] = \
                    self.user_get_ha1b(username, domain, password)
        else:
            insert_dict[USER_HA1_SHA256_COL] = \
                    self.user_get_ha1_sha256(username, domain, password)
            insert_dict[USER_HA1_SHA512T256_COL] = \
                    self.user_get_ha1_sha512t256(username, domain, password)

        insert_dict[USER_PASS_COL] = \
                password if cfg.getBool("plain_text_passwords") else ""

        db.insert(USER_TABLE, insert_dict)
        logger.info("Successfully added {}@{}".format(username, domain))

        db.destroy()
        return True

    def do_password(self, params=None, modifiers=None):

        if len(params) < 1:
            name = cfg.read_param(None,
                    "Please provide the username to change the password for")
            if not name:
                logger.error("empty username")
                return -1
        else:
            name = params[0]
        username, domain = self.user_get_domain(name)

        db, osips_ver = self.user_db_connect()
        if not db:
            return -1

        user_dict = {
                USER_NAME_COL: username,
                USER_DOMAIN_COL: domain
            }
        # check if the user already exists
        if not db.entry_exists(USER_TABLE, user_dict):
            logger.warning("User {}@{} does not exist".
                    format(username, domain))
            return -1

        if len(params) > 1:
            password = params[1]
        else:
            password = self.user_get_password()
            if password is None:
                logger.error("Password not specified: " +
                        "cannot change passowrd for user {}@{}".
                        format(user, domain))
                return -1
        plain_text_pw = cfg.getBool("plain_text_passwords")
        update_dict = {
                USER_HA1_COL: self.user_get_ha1(username, domain, password),
                USER_PASS_COL: password if plain_text_pw else ""
            }

        if osips_ver < '3.2':
            update_dict[USER_HA1B_COL] = self.user_get_ha1b(
                    username, domain, password)

        db.update(USER_TABLE, update_dict, user_dict)
        logger.info("Successfully changed password for {}@{}".
                        format(username, domain))
        db.destroy()
        return True

    def do_delete(self, params=None, modifiers=None):

        if len(params) < 1:
            name = cfg.read_param(None,
                    "Please provide the username you want to delete")
            if not name:
                logger.warning("no username to delete!")
                return -1
        else:
            name = params[0]
        username, domain = self.user_get_domain(name)

        db, _ = self.user_db_connect()
        if not db:
            return -1

        delete_dict = {
                USER_NAME_COL: username,
                USER_DOMAIN_COL: domain
            }
        # check if the user already exists
        if not db.entry_exists(USER_TABLE, delete_dict):
            logger.error("User {}@{} does not exist".
                    format(username, domain))
            return -1

        db.delete(USER_TABLE, delete_dict)
        logger.info("Successfully deleted {}@{}".format(username, domain))

        db.destroy()
        return True

    def __exclude__(self):
        if cfg.exists("dababase_user_url"):
            db_url = cfg.get("database_user_url")
        elif cfg.exists("database_url"):
            db_url = cfg.get("database_url")
        else:
            return (not osdb.has_sqlalchemy(), None)
        return (not osdb.has_dialect(osdb.get_dialect(db_url)), None)

