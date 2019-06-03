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
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy import Column, Date, Integer, String, Boolean
    from sqlalchemy.orm import sessionmaker, deferred
    sqlalchemy_available = True
except ImportError:
    logger.info("sqlalchemy and sqlalchemy_utils are not available!")
    sqlalchemy_available = False

"""
SQLAlchemy: Classes for ORM handling
"""
Base = declarative_base()

class Roles(Base):
    """
    Postgres: Roles database
    """
    __tablename__ = 'pg_roles'

    oid = Column(Integer, primary_key=True)
    rolname = Column(String)
    rolsuper = deferred(Column(Boolean), group='options')
    rolinherit = deferred(Column(Boolean), group='options')
    rolcreaterole = deferred(Column(Boolean), group='options')
    rolcreatedb = deferred(Column(Boolean), group='options')
    rolcanlogin = deferred(Column(Boolean), group='options')
    rolreplication = deferred(Column(Boolean), group='options')
    rolconnlimit = deferred(Column(Integer))
    rolpassword = Column(String)
    rolvaliduntil = deferred(Column(Date))
    rolbypassrls = deferred(Column(Boolean))
    rolconfig = deferred(Column(String))

    def __repr__(self):
        """
        returns a string from an arbitrary object
        """
        return self.shape

class osdbError(Exception):
    """
    OSDB: error handler
    """
    pass

class osdb(object):
    """
    Class: object store database
    """
    def __init__(self, db_url, db_name):
        """
        constructor
        """
        self.db_url = db_url
        self.db_name = db_name
        self.dialect = osdb.get_dialect(db_url)
        self.Session = sessionmaker()
        self.conn = None

        # TODO: do this only for SQLAlchemy
        try:
            if self.dialect == "postgresql":
                engine = sqlalchemy.create_engine(db_url, isolation_level='AUTOCOMMIT')
            else:
                engine = sqlalchemy.create_engine(db_url)
            self.conn = engine.connect()
            # connect the Session object to our engine
            self.Session.configure(bind=engine)
            # instanciate the Session object
            self.session = self.Session()
        except sqlalchemy.exc.OperationalError as se:
            logger.error("cannot connect to DB server: {}!".format(se))
            raise osdbError("unable to connect to the database") from None
        except sqlalchemy.exc.NoSuchModuleError:
            raise osdbError("cannot handle {} dialect".
                    format(self.dialect)) from None

    def alter_role(self, role_name="opensips", role_options="RESET ALL"):
        """
        alter attributes of a role object
        """
        # TODO: is any other dialect using the "role" concept?
        if self.dialect != "postgres":
            return False

        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")
            return False

        logger.debug("Role {} will be granted with options '{}' on database {}".
                format(role_name, role_options, self.db_name))

        #sqlcmd = "ALTER ROLE {} IN DATABASE {} TO {} SET {} = ".format(role_name, self.db_name, role_options)
        sqlcmd = "ALTER ROLE {} WITH {} ".format(role_name, role_options)
        try:
            result = self.conn.execute(sqlcmd)
            if result:
                logger.debug("granted options '{}' to role '{}'".
                    format(role_options, role_name))
        except:
            logger.error("granting options '{}' to role '{}' failed".
                    format(role_options, role_name))
            return False
        return

    def create(self):
        """
        create a database object
        """
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")
        # all good - it's time to create the database
        if self.dialect == "postgres":
            logger.debug("Create Database '{}' for dialect: '{}'".
                    format(self.db_name, self.dialect))
            self.conn.connection.connection.set_isolation_level(0)
            try:
                self.conn.execute("CREATE DATABASE {} WITH TEMPLATE template1".format(self.db_name))
                logger.info("Database '%s' for dialect '%s' created", self.db_name, self.dialect)
                self.conn.connection.connection.set_isolation_level(1)
            except sqlalchemy.exc.OperationalError as se:
                logger.error("cannot create database: {}!".format(se))
            #raise osdbError("unable to connect to the database") from None
        else:
            self.conn.execute("CREATE DATABASE {}".format(self.db_name))
        return True

    def create_module(self, import_file):
        """
        create a module object
        """
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")

        logger.debug("create_module: '%s'", import_file)
        with open(import_file, 'r') as f:
            try:
                #schema = f.read()
                #logger.debug("schema: '%s'", schema)
                #self.conn.execute(schema)
                self.conn.execute(f.read())
            except sqlalchemy.exc.IntegrityError as ie:
                raise osdbError("cannot deploy {} file: {}".
                        format(import_file, ie)) from None

    def create_role(self, role_name, role_options, role_password):
        """
        create a role object (PostgreSQL secific)
        """
        # TODO: is any other dialect using the "role" concept?
        if self.dialect != "postgres":
            return False

        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")
            return False

        sqlcmd = "CREATE ROLE {} WITH {} PASSWORD '{}'".\
            format(role_name, role_options, role_password)
        try:
            result = self.conn.execute(sqlcmd)
            if result:
                logger.info("role '{}' with options '{}' created".
                    format(role_name, role_options))
        except:
            logger.error("creation of new role '%s' with options '%s' failed",
                    role_name, role_options)
            return False
        return

    def delete(self, table, filter_keys=None):
        """
        delete a table object from a database
        """
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")

        where_str = self.get_where(filter_keys)
        statement = "DELETE FROM {}{}".format(table, where_str)
        try:
            self.conn.execute(statement)
        except sqlalchemy.exc.SQLAlchemyError as ex:
            logger.error("cannot execute query: {}".format(statement))
            logger.error(ex)
            return False
        return True

    def destroy(self):
        """
        decontructor of a database object
        """
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            return
        self.session.close()
        self.conn.close()

    def drop(self):
        """
        drop a database object
        """
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

    def drop_role(self, role_name):
        """
        drop a role object (PostgreSQL specific)
        """
        # TODO: is any other dialect using the "role" concept?
        if self.dialect != "postgres":
            return False

        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")
            return False

        logger.debug("Role '%s' will be dropped", role_name)

        sqlcmd = "DROP ROLE IF EXISTS {}".format(role_name)
        try:
            result = self.conn.execute(sqlcmd)
            if result:
                logger.debug("Role '%s' dropped", role_name)
        except:
            logger.error("dropping role '%s' failed", role_name)
            return False
        return

    def entry_exists(self, table, constraints):
        """
        check for existence of table constraints
        """
        ret = self.find(table, "count(*)", constraints)
        if ret and ret.first()[0] != 0:
            return True
        return False

    def exists(self):
        """
        check for existence of a database object
        """
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")
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

    def exists_role(self, role_name="opensips"):
        """
        check for existence of a role object (PostgreSQL specific)
        """
        # TODO: is any other dialect using the "role" concept?
        if self.dialect != "postgres":
            return False

        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")
            return False

        filter_args = { 'rolname':role_name }
        logger.debug("filter argument: '%s'", filter_args)

        role_count = self.session.query(Roles).\
                filter_by(**filter_args).\
                count()
        logger.debug("Number of matching role instances: '%s'", role_count)

        if role_count >= 1:
            logger.debug("Role instance '%s' exists", role_name)
            return True
        else:
            logger.debug("Role instance '%s' does not exist", role_name)
            return False

    def find(self, table, fields, filter_keys):
        """
        match fields in a given table
        """
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")
        if not fields:
            fields = ['*']
        elif type(fields) != list:
            fields = [ fields ]

        where_str = self.get_where(filter_keys)
        statement = "SELECT {} FROM {}{}".format(
                ", ".join(fields),
                table,
                where_str)
        try:
            result = self.conn.execute(statement)
        except sqlalchemy.exc.SQLAlchemyError as ex:
            logger.error("cannot execute query: {}".format(statement))
            logger.error(ex)
            return None
        return result

    def get_dialect(url):
        """
        extract database dialect from an url
        """
        return url.split('://')[0]

    def get_where(self, filter_keys):
        """
        construct a sql 'where clause' from given filter keys
        """
        if filter_keys:
            where_str = ""
            for k, v in filter_keys.items():
                where_str += " AND {} = ".format(k)
                if type(v) == int:
                    where_str += v
                else:
                    where_str += "'{}'".format(
                            v.translate(str.maketrans({'\'': '\\\''})))
            if where_str != "":
                where_str = " WHERE " + where_str[5:]
        else:
            where_str = ""
        return where_str

    def get_role(self, role_name="opensips"):
        """
        get attibutes of a role object (PostgreSQL specific)
        """
        # TODO: is any other dialect using the "role" concept?
        if self.dialect != "postgres":
            return False

        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")
            return False

        # query elements for the given role
        role_element = self.session.query(Roles).\
            filter(Roles.rolname == role_name).all()

        # create a dictionary and output the key-value pairs
        for row in role_element:
            #print ("role: ", row.rolname, "(password:", row.rolpassword, "canlogin:", row.rolcanlogin, ")")
            dict = self.row2dict(row)
        for key in sorted(dict, key=lambda k: dict[k], reverse=True):
            print (key + ": " + dict[key])
        logger.debug("role_elements: %s", dict)

    def grant_db_options(self, role_name="opensips", role_options="ALL PRIVILEGES"):
        """
        assign attibutes to a role object (PostgreSQL specific)
        """
        # TODO: is any other dialect using the "role" concept?
        if self.dialect != "postgres":
            return False

        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")
            return False

        #role_options = "CREATE, CONNECT, DELETE, EXECUTE, INSERT, SELECT, REFERENCES, TEMPORARY, TRIGGER, TRUNCATE, UPDATE, USAGE"
        logger.debug("Role {} will be granted with options '{}' on database {}".
                format(role_name, role_options, self.db_name))

        sqlcmd = "GRANT {} ON DATABASE {} TO {}".format(role_options, self.db_name, role_name)
        try:
            result = self.conn.execute(sqlcmd)
            if result:
                logger.info("granted options '{}' to role '{}' on database '{}'".
                    format(role_options, role_name, self.db_name))
        except:
            logger.error("granting options '{}' to role '{}' on database '{}' failed".
                    format(role_options, role_name, self.db_name))
            return False
        return

    def has_sqlalchemy():
        """
        check for usability of the SQLAlchemy modules
        """
        logger.debug("SQLAlchemy version: %s", sqlalchemy.__version__)
        return sqlalchemy_available

    def has_dialect(dialect):
        """
        check for support of a given database dialect via SQLAlchemy
        """
        # TODO: do this only for SQLAlchemy
        try:
            result = sqlalchemy.create_engine('{}://'.format(dialect))
        except sqlalchemy.exc.NoSuchModuleError:
            return False
        return result

    def insert(self, table, keys):
        """
        insert values into table
        """
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")

        values = ""
        for v in keys.values():
            values += ", "
            if type(v) == int:
                values += v
            else:
                values += "'{}'".format(
                        v.translate(str.maketrans({'\'': '\\\''})))
        statement = "INSERT INTO {} ({}) VALUES ({})".format(
                table, ", ".join(keys.keys()), values[2:])
        try:
            result = self.conn.execute(statement)
        except sqlalchemy.exc.SQLAlchemyError as ex:
            logger.error("cannot execute query: {}".format(statement))
            logger.error(ex)
            return False
        return result

    def row2dict(self, row):
        dict = {}
        for column in row.__table__.columns:
            dict[column.name] = str(getattr(row, column.name))

        return dict

    def update(self, table, update_keys, filter_keys=None):
        """
        update values of given table
        """
        # TODO: do this only for SQLAlchemy
        if not self.conn:
            raise osdbError("connection not available")

        update_str = ""
        for k, v in update_keys.items():
            update_str += ", {} = ".format(k)
            if type(v) == int:
                update_str += v
            else:
                update_str += "'{}'".format(
                        v.translate(str.maketrans({'\'': '\\\''})))
        where_str = self.get_where(filter_keys)
        statement = "UPDATE {} SET {}{}".format(table,
                update_str[2:], where_str)
        try:
            result = self.conn.execute(statement)
        except sqlalchemy.exc.SQLAlchemyError as ex:
            logger.error("cannot execute query: {}".format(statement))
            logger.error(ex)
            return False
        return result

    def connect(self):
        """
        connect to database
        """
        # TODO: do this only for SQLAlchemy
        if self.dialect == "postgres":
            database_url = "{}/{}".format(self.db_url, self.db_name)
            if sqlalchemy_utils.database_exists(database_url) is True:
                engine = sqlalchemy.create_engine(database_url, isolation_level='AUTOCOMMIT')
                self.conn = engine.connect()
                # connect the Session object to our engine
                self.Session.configure(bind=engine)
                # instanciate the Session object
                self.session = self.Session()
                logger.warning("connected to database URL '%s'", database_url)
        else:
            self.conn.execute("USE {}".format(self.db_name))
