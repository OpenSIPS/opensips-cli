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
from opensipscli.config import cfg
import re

try:
    import sqlalchemy
    import sqlalchemy_utils
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy import Column, Date, Integer, String, Boolean
    from sqlalchemy.orm import sessionmaker, deferred
    from sqlalchemy.engine.url import make_url
    sqlalchemy_available = True
    logger.debug("SQLAlchemy version: ", sqlalchemy.__version__)
except ImportError:
    logger.info("sqlalchemy and sqlalchemy_utils are not available!")
    sqlalchemy_available = False

SUPPORTED_BACKENDS = [
    "mysql",
    "postgres",
    "sqlite",
    "oracle",
]

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

class osdbModuleAlreadyExistsError(osdbError):
    """
    OSDB: module error handler
    """
    pass

class osdbAccessDeniedError(osdbError):
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

            logger.debug("connecting to %s", db_url)
            self.__conn = self.__engine.connect().\
                    execution_options(autocommit=True)
            # connect the Session object to our engine
            self.Session.configure(bind=self.__engine)
            # instanciate the Session object
            self.__session = self.Session()
        except sqlalchemy.exc.OperationalError as se:
            if self.dialect == "mysql":
                try:
                    if int(se.args[0].split(",")[0].split("(")[2]) in [
                            2006, # MySQL
                            1044, # MariaDB
                            1045, # MariaDB
                            ]:
                        raise osdbAccessDeniedError
                except osdbAccessDeniedError:
                    raise
                except:
                    logger.error("unexpected parsing exception")
            elif self.dialect == "postgres" and \
                    (("authentication" in se.args[0] and "failed" in se.args[0]) or \
                     ("no password supplied" in se.args[0])):
                raise osdbAccessDeniedError

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
            self.db_url = self.set_url_db(self.db_url, self.db_name)
            if sqlalchemy_utils.database_exists(self.db_url) is True:
                engine = sqlalchemy.create_engine(self.db_url, isolation_level='AUTOCOMMIT')
                if self.__conn:
                    self.__conn.close()
                self.__conn = engine.connect()
                # connect the Session object to our engine
                self.Session.configure(bind=self.__engine)
                # instanciate the Session object
                self.session = self.Session()
                logger.debug("connected to database URL '%s'", self.db_url)
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

        logger.debug("Create Database '%s' for dialect '%s' ...",
                     self.db_name, self.dialect)

        # all good - it's time to create the database
        if self.dialect == "postgres":
            self.__conn.connection.connection.set_isolation_level(0)
            try:
                self.__conn.execute("CREATE DATABASE {}".format(self.db_name))
                self.__conn.connection.connection.set_isolation_level(1)
            except sqlalchemy.exc.OperationalError as se:
                logger.error("cannot create database: {}!".format(se))
        else:
            self.__conn.execute("CREATE DATABASE {}".format(self.db_name))

        logger.debug("success")
        return True

    def create_module(self, import_file):
        """
        create a module object
        """
        self.exec_sql_file(import_file)

    def ensure_user(self, db_url):
        url = make_url(db_url)
        if url.password is None:
            logger.error("database URL does not include a password")
            return False

        if url.drivername.lower() == "mysql":
            sqlcmd = """CREATE USER IF NOT EXISTS '{}'@'{}' IDENTIFIED
                        BY '{}'""".format(url.username, url.host, url.password)
            try:
                result = self.__conn.execute(sqlcmd)
                if result:
                    logger.info("created user '%s'@'%s'",
                                url.username, url.host)
            except:
                logger.error("failed to create user '%s'@'%s'",
                                url.username, url.host)
                return False

            sqlcmd = "SET PASSWORD FOR '{}'@'{}' = PASSWORD('{}')".format(
                        url.username, url.host, url.password)
            try:
                result = self.__conn.execute(sqlcmd)
                if result:
                    logger.info("set password for '%s'@'%s'",
                                url.username, url.host)
            except:
                logger.error("failed to set password for '%s'@'%s'",
                                url.username, url.host)
                return False

            sqlcmd = "GRANT ALL ON {}.* TO '{}'@'{}'".format(
                     self.db_name, url.username, url.host)
            try:
                result = self.__conn.execute(sqlcmd)
                if result:
                    logger.info("granted access to '%s'@'%s' on '%s'",
                                url.username, url.host, self.db_name)
            except:
                logger.error("failed to grant access to '%s'@'%s'",
                                url.username, url.host)
                return False

            sqlcmd = "FLUSH PRIVILEGES"
            try:
                result = self.__conn.execute(sqlcmd)
                logger.info("flushed privileges")
            except:
                logger.error("failed to flush privileges")
                return False
        elif url.drivername.lower() == "postgres":
            if not self.exists_role(url.username):
                logger.info("creating role %s", url.username)
                if not self.create_role(url.username, url.password):
                    logger.error("failed to create role %s", url.username)

            self.create_role(url.username, url.password, update=True)

            sqlcmd = "GRANT ALL PRIVILEGES ON DATABASE {} TO {}".format(
                        self.db_name, url.username)
            logger.info(sqlcmd)

            try:
                result = self.__conn.execute(sqlcmd)
                if result:
                    logger.debug("... OK")
            except:
                logger.error("failed to grant ALL to '%s' on db '%s'",
                        url.username, self.db_name)
                return False

        return True

    def create_role(self, role_name, role_password, update=False,
                    role_options="NOCREATEDB NOCREATEROLE LOGIN"):
        """
        create a role object (PostgreSQL secific)
        """
        # TODO: is any other dialect using the "role" concept?
        if self.dialect != "postgres":
            return False

        # TODO: do this only for SQLAlchemy
        if not self.__conn:
            raise osdbError("connection not available")

        if update:
            sqlcmd = "ALTER USER {} WITH PASSWORD '{}' {}".format(
                    role_name, role_password, role_options)
        else:
            sqlcmd = "CREATE ROLE {} WITH {} PASSWORD '{}'".format(
                    role_name, role_options, role_password)
        logger.info(sqlcmd)

        try:
            result = self.__conn.execute(sqlcmd)
            if result:
                logger.info("role '{}' with options '{}' created".
                    format(role_name, role_options))
        except Exception as e:
            logger.exception(e)
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
        database_url = self.set_url_db(self.db_url, self.db_name)
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
            if sql_file.endswith("-migrate.sql"):
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
            else:
                for sql in f.read().split(";"):
                    sql = sql.strip()
                    if not sql:
                        continue
                    try:
                        self.__conn.execute(sql)
                    except sqlalchemy.exc.IntegrityError as ie:
                        raise osdbModuleAlreadyExistsError(
                            "cannot deploy {} file: {}".format(sql_file, ie)) from None

    def exists(self, db=None):
        """
        check for existence of a database object
        """
        check_db = db if db is not None else self.db_name
        # TODO: do this only for SQLAlchemy
        if not self.__conn:
            return False

        database_url = self.set_url_db(self.db_url, check_db)
        logger.debug("check database URL '{}'".format(database_url))

        try:
            if sqlalchemy_utils.database_exists(database_url):
                logger.debug("DB '{}' exists".format(check_db))
                return True
        except sqlalchemy.exc.NoSuchModuleError as me:
            logger.error("cannot check if database {} exists: {}".
                    format(check_db, me))
            raise osdbError("cannot handle {} dialect".
                    format(self.dialect)) from None

        logger.debug("DB does not exist")
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

        filter_args = {'rolname': role_name}
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

        return True

    def grant_table_options(self, role, table, privs="ALL PRIVILEGES"):
        if self.dialect != "postgres":
            return False

        if not self.__conn:
            raise osdbError("connection not available")

        sqlcmd = "GRANT {} ON TABLE {} TO {}".format(privs, table, role)
        logger.info(sqlcmd)

        try:
            result = self.__conn.execute(sqlcmd)
        except Exception as e:
            logger.exception(e)
            logger.error("failed to grant '%s' to '%s' on table '%s'",
                         privs, role, table)
            return False

        return True

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

    def migrate(self, proc_suffix, migrate_scripts, old_db, new_db, tables=[]):
        """
        migrate from source to destination database using SQL schema files
        @flavour: values should resemble: '2.4_to_3.0', '3.0_to_3.1'
        @sp_suffix: stored procedure name suffix, specific to each migration
        """

        if self.dialect != "mysql":
            logger.error("Table data migration is only supported for MySQL!")
            return

        proc_db_migrate = 'OSIPS_DB_MIGRATE_{}'.format(proc_suffix)
        proc_tb_migrate = 'OSIPS_TB_COPY_{}'.format(proc_suffix)

        self.connect(old_db)

        """ drop DB/table migration stored procedures if already present """
        try:
            ret = self.find('mysql.proc', "count(*)",
                        {'db': old_db, 'name': proc_db_migrate})
            if ret and ret.first()[0] != 0:
                self.__conn.execute(sqlalchemy.sql.text(
                    "DROP PROCEDURE IF EXISTS {}".format(proc_db_migrate)).
                        execution_options(autocommit=True))

            ret = self.find('mysql.proc', "count(*)",
                        {'db': old_db, 'name': proc_tb_migrate})
            if ret and ret.first()[0] != 0:
                self.__conn.execute(sqlalchemy.sql.text(
                    "DROP PROCEDURE IF EXISTS {}".format(proc_tb_migrate)).
                        execution_options(autocommit=True))
        except Exception as e:
            logger.exception(e)
            logger.error("Failed to re-create migration stored procedures!")

        for ms in migrate_scripts:
            logger.debug("Importing {}...".format(ms))
            self.exec_sql_file(ms)

        if tables:
            for tb in tables:
                logger.info("Migrating {} data... ".format(tb))
                try:
                    self.__conn.execute(sqlalchemy.sql.text(
                        "CALL {}.{}('{}', '{}', '{}')".format(
                            old_db, proc_tb_migrate, old_db, new_db, tb)))
                except Exception as e:
                    logger.exception(e)
                    logger.error("Failed to migrate '{}' table data, ".format(tb) +
                                    "see above errors!")
        else:
            try:
                self.__conn.execute(sqlalchemy.sql.text(
                    "CALL {}.{}('{}', '{}')".format(
                        old_db, proc_db_migrate, old_db, new_db)))
            except Exception as e:
                logger.exception(e)
                logger.error("Failed to migrate database!")

        print("Finished copying OpenSIPS table data " +
                "into database '{}'!".format(new_db))

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


    @staticmethod
    def get_db_engine():
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


    @staticmethod
    def get_db_host():
        if cfg.exists('database_admin_url'):
            return osdb.get_url_host(cfg.get('database_admin_url'))
        elif cfg.exists('database_url'):
            return osdb.get_url_host(cfg.get('database_url'))

        return "localhost"


    @staticmethod
    def set_url_db(url, db):
        """
        Force a given database @url string to include the given @db
        """
        at_idx = url.find('@')
        if at_idx < 0:
            logger.error("Bad database URL: {}, missing host part".format(url))
            return None

        db_idx = url.find('/', at_idx)
        if db_idx < 0:
            return url + '/' + db
        else:
            return url[:db_idx+1] + db


    @staticmethod
    def set_url_driver(url, driver):
        return driver + url[url.find(':'):]


    @staticmethod
    def set_url_password(url, password):
        url = make_url(url)
        url.password = password
        return str(url)


    @staticmethod
    def set_url_host(url, host):
        url = make_url(url)
        url.host = host
        return str(url)


    @staticmethod
    def get_url_driver(url, capitalize=False):
        if capitalize:
            driver = make_url(url).drivername.lower()
            capitalized = {
                'mysql': 'MySQL',
                'postgres': 'PostgreSQL',
                'sqlite': 'SQLite',
                'oracle': 'Oracle',
                }
            return capitalized.get(driver, driver.capitalize())
        else:
            return make_url(url).drivername.lower()


    @staticmethod
    def get_url_user(url):
        return make_url(url).username


    @staticmethod
    def get_url_pswd(url):
        return make_url(url).password


    @staticmethod
    def get_url_host(url):
        return make_url(url).host
