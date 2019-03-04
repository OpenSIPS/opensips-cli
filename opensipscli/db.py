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

from opensipscli.logger import logger

try:
    import sqlalchemy
    import sqlalchemy_utils
    sqlalchemy_available = True
except ImportError:
    logger.info("sqlalchemy and sqlalchemy_utils are not available!")
    sqlalchemy_available = False

class osdbError(Exception):
    pass

class osdb(object):

    def get_dialect(url):
        return url.split('://')[0]

    def has_sqlalchemy():
        return sqlalchemy_available

    def __init__(self, db_url, db_name):
        self.db_url = db_url
        self.db_name = db_name
        self.dialect = osdb.get_dialect(db_url)
        self.conn = None

        # TODO: do this only for SQLAlchemy
        try:
            engine = sqlalchemy.create_engine(db_url)
            self.conn = engine.connect()
        except sqlalchemy.exc.OperationalError as se:
            logger.error("cannot connect to DB server: {}!".format(se))
            raise osdbError("unable to connect to the database") from None
        except sqlalchemy.exc.NoSuchModuleError as me:
            raise osdbError("cannot handle {} dialect".
                    format(self.dialect)) from None

    def exists(self):
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            return False
        database_url = "{}/{}".format(self.db_url, self.db_name)
        try:
            if sqlalchemy_utils.database_exists(database_url):
                return True
        except sqlalchemy.exc.NoSuchModuleError as me:
            logger.error("cannot check if database {} exists: {}".
                    format(self.db_name, me))
            raise osdbError("cannot handle {} dialect".
                    format(self.dialect)) from None
        return False

    def destroy(self):
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            return
        self.conn.close()

    def drop(self):
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")
        database_url = "{}/{}".format(self.db_url, self.db_name)
        try:
            if sqlalchemy_utils.drop_database(database_url):
                return True
        except sqlalchemy.exc.NoSuchModuleError as me:
            logger.error("cannot check if database {} exists: {}".
                    format(self.db_name, me))
            raise osdbError("cannot handle {} dialect".
                    format(self.dialect)) from None

    def create(self):
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")
        # all good - it's time to create the database
        self.conn.execute("CREATE DATABASE {}".format(self.db_name))

    def use(self):
        self.conn.execute("USE {}".format(self.db_name))

    def create_module(self, import_file):
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")

        with open(import_file, 'r') as f:
            try:
                self.conn.execute(f.read())
            except sqlalchemy.exc.IntegrityError as ie:
                raise osdbError("cannot deploy {} file: {}".
                        format(import_file, ie)) from None

