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
import re

try:
    import sqlalchemy
    import sqlalchemy_utils
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy import Column, Date, Integer, String, Boolean
    from sqlalchemy.orm import sessionmaker, deferred
    sqlalchemy_available = True
    logger.debug("SQLAlchemy version: ", sqlalchemy.__version__)
except ImportError:
    logger.info("sqlalchemy and sqlalchemy_utils are not available!")
    sqlalchemy_available = False

"""
SQLAlchemy: Classes for ORM handling
"""
if sqlalchemy_available:
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

class osdbConnectError(osdbError):
    """
    OSDB: connecton error handler
    """
    pass

class osdbArgumentError(osdbError):
    """
    OSDB: argument error handler
    """
    pass

class osdbNoSuchModuleError(osdbError):
    """
    OSDB: module error handler
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
        self.__engine = None
        self.__conn = None

	    # TODO: do this only for SQLAlchemy
        try:
            if self.dialect == "postgresql":
                self.__engine = sqlalchemy.create_engine(db_url, isolation_level='AUTOCOMMIT')
            else:
                self.__engine = sqlalchemy.create_engine(db_url)
            self.__conn = self.__engine.connect()
            # connect the Session object to our engine
            self.Session.configure(bind=self.__engine)
            # instanciate the Session object
            self.__session = self.Session()
        except sqlalchemy.exc.OperationalError as se:
            logger.error("cannot connect to DB server: {}!".format(se))
            raise osdbError("unable to connect to the database")
        except sqlalchemy.exc.NoSuchModuleError:
            raise osdbError("cannot handle {} dialect".
                    format(self.dialect))
        except sqlalchemy.exc.ArgumentError:
            raise osdbArgumentError("bad DB URL: {}".format(
                self.db_url))

    def alter_role(self, role_name, role_options=None, role_password=None):
        """
        alter attributes of a role object
        """
        # TODO: is any other dialect using the "role" concept?
        if self.dialect != "postgres":
            return False

        # TODO: do this only for SQLAlchemy
        if not self.__conn:
            raise osdbError("connection not available")
            return False

        if not role_options is None:
            sqlcmd = "ALTER ROLE {} WITH {}".format(role_name, role_options)
            msg = "Alter role '{}' with options '{}'". \
                format(role_name, role_options, self.db_name)
        if not role_password is None:
            sqlcmd  += " PASSWORD '{}'".format(role_password)
            msg += " and password '********'"
        msg += " on database '{}'".format(self.db_name)
        try:
            result = self.__conn.execute(sqlcmd)
            if result:
                logger.info( "{} was successfull".format(msg))
        except:
            logger.error("%s failed", msg)
            return False
        return

    def connect(self, db_name=None):
        """
        connect to database
        """
        if db_name is not None:
            self.db_name = db_name
		# TODO: do this only for SQLAlchemy
        if self.dialect == "postgres":
            database_url = "{}/{}".format(self.db_url, self.db_name)
            if sqlalchemy_utils.database_exists(database_url) is True:
                engine = sqlalchemy.create_engine(database_url, isolation_level='AUTOCOMMIT')
                self.__conn = engine.connect()
                # connect the Session object to our engine
                self.Session.configure(bind=self.__engine)
                # instanciate the Session object
                self.session = self.Session()
                logger.warning("connected to database URL '%s'", database_url)
        else:
            self.__conn.execute("USE {}".format(self.db_name))

    def create(self, db_name=None):
        """
        create a database object
        """
        if db_name is None:
            db_name = self.db_name
        # TODO: do this only for SQLAlchemy
        if not self.__conn:
            raise osdbError("connection not available")
        # all good - it's time to create the database
        if self.dialect == "postgres":
            logger.debug("Create Database '%s' for dialect: '%s'",
                self.db_name, self.dialect)
            self.__conn.connection.connection.set_isolation_level(0)
            try:
                self.__conn.execute("CREATE DATABASE {} WITH TEMPLATE template1".format(self.db_name))
                logger.info("Database '%s' for dialect '%s' created", self.db_name, self.dialect)
                self.__conn.connection.connection.set_isolation_level(1)
            except sqlalchemy.exc.OperationalError as se:
                logger.error("cannot create database: {}!".format(se))
        else:
            self.__conn.execute("CREATE DATABASE {}".format(self.db_name))
        return True

    def create_module(self, import_file):
        """
        create a module object
        """
        self.exec_sql_file(import_file)

    def create_role(self, role_name, role_options, role_password):
        """
        create a role object (PostgreSQL secific)
        """
        # TODO: is any other dialect using the "role" concept?
        if self.dialect != "postgres":
            return False

        # TODO: do this only for SQLAlchemy
        if not self.__conn:
            raise osdbError("connection not available")
            return False

        sqlcmd = "CREATE ROLE {} WITH {} PASSWORD '{}'".\
            format(role_name, role_options, role_password)
        try:
            result = self.__conn.execute(sqlcmd)
            if result:
                logger.info("role '{}' with options '{}' created".
                    format(role_name, role_options))
        except:
            logger.error("creation of new role '%s' with options '%s' failed",
                    role_name, role_options)
            return False
        return result

    def delete(self, table, filter_keys=None):
        """
        delete a table object from a database
        """
        # TODO: do this only for SQLAlchemy
        if not self.__conn:
            raise osdbError("connection not available")

        where_str = self.get_where(filter_keys)
        statement = "DELETE FROM {}{}".format(table, where_str)
        try:
            self.__conn.execute(statement)
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
       if not self.__conn:
            return
       self.__conn.close()

    def drop(self):
        """
        drop a database object
        """
        # TODO: do this only for SQLAlchemy
        if not self.__conn:
            raise osdbError("connection not available")
        database_url = "{}/{}".format(self.db_url, self.db_name)
        try:
            sqlalchemy_utils.drop_database(database_url)
            logger.debug("database '%s' dropped", self.db_name)
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
        if not self.__conn:
            raise osdbError("connection not available")
            return False

        logger.debug("Role '%s' will be dropped", role_name)

        sqlcmd = "DROP ROLE IF EXISTS {}".format(role_name)
        try:
            result = self.__conn.execute(sqlcmd)
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

    def exec_sql_file(self, sql_file):
        """
        deploy given sql file
        """
        # TODO: do this only for SQLAlchemy
        if not self.__conn:
            raise osdbError("connection not available")

        with open(sql_file, 'r') as f:
            try:
                sql = f.read()

                # the DELIMITER thingies are only useful to mysql shell client
                sql = re.sub(r'DELIMITER .*\n', '', sql)
                sql = re.sub(r'\$\$', ';', sql)

                # DROP/CREATE PROCEDURE statements seem to only work separately
                sql = re.sub(r'DROP PROCEDURE .*\n', '', sql)

                self.__conn.execute(sql)
            except sqlalchemy.exc.IntegrityError as ie:
                raise osdbError("cannot deploy {} file: {}".
                        format(sql_file, ie)) from None

    def exists(self, db=None):
        """
        check for existence of a database object
        """
        check_db = db if db is not None else self.db_name
        # TODO: do this only for SQLAlchemy
        if not self.__conn:
            return False
        database_url = "{}/{}".format(self.db_url, check_db)
        logger.debug("check database URL '%s'!", database_url)

        try:
            if sqlalchemy_utils.database_exists(database_url):
                return True
        except sqlalchemy.exc.NoSuchModuleError as me:
            logger.error("cannot check if database {} exists: {}".
                    format(check_db, me))
            raise osdbError("cannot handle {} dialect".
                    format(self.dialect)) from None
        return False

    def exists_role(self, role_name=None):
        """
        check for existence of a role object (PostgreSQL specific)
        """
        # TODO: is any other dialect using the "role" concept?
        if self.dialect != "postgres":
            return False

        # TODO: do this only for SQLAlchemy
        if not self.__conn:
            raise osdbError("connection not available")
            return False

        if role_name is None:
            role_name = 'opensips'

        filter_args = { 'rolname':role_name }
        logger.debug("filter argument: '%s'", filter_args)

        role_count = self.__session.query(Roles).\
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
        if not self.__conn:
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
            result = self.__conn.execute(statement)
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
        if not self.__conn:
            raise osdbError("connection not available")
            return False

        # query elements for the given role
        role_element = self.__session.query(Roles).\
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
        if not self.__conn:
            raise osdbError("connection not available")
            return False

        logger.debug("Role '%s' will be granted with options '%s' on database '%s'",
					 role_name, role_options, self.db_name)

        sqlcmd = "GRANT {} ON DATABASE {} TO {}".format(role_options, self.db_name, role_name)
        try:
            result = self.__conn.execute(sqlcmd)
            if result:
                logger.info("granted options '%s' to role '%s' on database '%s'",
                    role_options, role_name, self.db_name)
        except:
            logger.error("granting options '%s' to role '%s' on database '%s' failed",
                    role_options, role_name, self.db_name)
            return False
        return

    def has_sqlalchemy():
        """
        check for usability of the SQLAlchemy modules
        """
        return sqlalchemy_available

    def has_dialect(dialect):
        """
        check for support of a given database dialect via SQLAlchemy
        """
        # TODO: do this only for SQLAlchemy
        try:
            sqlalchemy.create_engine('{}://'.format(dialect))
        except sqlalchemy.exc.NoSuchModuleError:
            return False
        return True

    def insert(self, table, keys):
        """
        insert values into table
        """
        # TODO: do this only for SQLAlchemy
        if not self.__conn:
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
            result = self.__conn.execute(statement)
        except sqlalchemy.exc.SQLAlchemyError as ex:
            logger.error("cannot execute query: {}".format(statement))
            logger.error(ex)
            return False
        return result

    def migrate(self, migrate_scripts, old_db, new_db, tables=[]):
        if self.dialect != "mysql":
            logger.error("Table data migration is only supported for MySQL!")
            return

        """
        migrate from source to destination database using SQL schema files
        """
        self.connect(old_db)

        try:
            ret = self.find('mysql.proc', "count(*)",
                        {'db': old_db, 'name': 'OSIPS_DB_MIGRATE_2_4_TO_3_0'})
            if ret and ret.first()[0] != 0:
                self.__conn.execute(sqlalchemy.sql.text(
                    "DROP PROCEDURE IF EXISTS OSIPS_DB_MIGRATE_2_4_TO_3_0").
                        execution_options(autocommit=True))

            ret = self.find('mysql.proc', "count(*)",
                        {'db': old_db, 'name': 'OSIPS_TB_COPY_2_4_TO_3_0'})
            if ret and ret.first()[0] != 0:
                self.__conn.execute(sqlalchemy.sql.text(
                    "DROP PROCEDURE IF EXISTS OSIPS_TB_COPY_2_4_TO_3_0").
                        execution_options(autocommit=True))
        except Exception as e:
            logger.exception(e)
            logger.error("Failed to re-create migration stored procedures!")

        for ms in migrate_scripts:
            logger.debug("Importing {}...".format(ms))
            self.exec_sql_file(ms)

        if tables:
            for tb in tables:
                print("Migrating {} data... ".format(tb), end='')
                try:
                    self.__conn.execute(sqlalchemy.sql.text(
                        "CALL {}.OSIPS_TB_COPY_2_4_TO_3_0('{}', '{}', '{}')".format(
                            old_db, old_db, new_db, tb)).execution_options(
                                autocommit=True))
                    print("OK")
                except Exception as e:
                    print("FAILED!")
                    logger.exception(e)
                    logger.error("Failed to migrate '{}' table data, ".format(tb) +
                                    "see above errors!")
        else:
            try:
                self.__conn.execute(sqlalchemy.sql.text(
                    "CALL {}.OSIPS_DB_MIGRATE_2_4_TO_3_0('{}', '{}')".format(
                        old_db, old_db, new_db)).execution_options(
                            autocommit=True))
            except Exception as e:
                logger.exception(e)
                logger.error("Failed to migrate database!")

    def row2dict(self, row):
        """
        convert SQL table row to python dict
        """
        dict = {}
        for column in row.__table__.columns:
            dict[column.name] = str(getattr(row, column.name))

        return dict

    def update(self, table, update_keys, filter_keys=None):
        """
        update table
        """
        # TODO: do this only for SQLAlchemy
        if not self.__conn:
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
            result = self.__conn.execute(statement)
        except sqlalchemy.exc.SQLAlchemyError as ex:
            logger.error("cannot execute query: {}".format(statement))
            logger.error(ex)
            return False
        return result
