## Copyright (c) 2012, Konsta Vesterinen
##
## All rights reserved.
##
## Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are met:
##
## * Redistributions of source code must retain the above copyright notice, this
##   list of conditions and the following disclaimer.
##
## * Redistributions in binary form must reproduce the above copyright notice,
##   this list of conditions and the following disclaimer in the documentation
##   and/or other materials provided with the distribution.
##
## * The names of the contributors may not be used to endorse or promote products
##   derived from this software without specific prior written permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
## ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
## WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
## DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY DIRECT,
## INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
## BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
## LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
## OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
## ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
##
## Copied from https://github.com/kvesteri/sqlalchemy-utils/blob/2e8ee0093f4a33a5c7479bc9aaf16d7863a74a16/sqlalchemy_utils/functions/database.py
## Please check LICENSE

from copy import copy

import os
import sqlalchemy as sa
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.orm.session import object_session
from sqlalchemy.orm.exc import UnmappedInstanceError

def database_exists(url):
    """Check if a database exists.
    :param url: A SQLAlchemy engine URL.
    Performs backend-specific testing to quickly determine if a database
    exists on the server. ::
        database_exists('postgresql://postgres@localhost/name')  #=> False
        create_database('postgresql://postgres@localhost/name')
        database_exists('postgresql://postgres@localhost/name')  #=> True
    Supports checking against a constructed URL as well. ::
        engine = create_engine('postgresql://postgres@localhost/name')
        database_exists(engine.url)  #=> False
        create_database(engine.url)
        database_exists(engine.url)  #=> True
    """

    def get_scalar_result(engine, sql):
        result_proxy = engine.execute(sql)
        result = result_proxy.scalar()
        result_proxy.close()
        engine.dispose()
        return result

    def sqlite_file_exists(database):
        if not os.path.isfile(database) or os.path.getsize(database) < 100:
            return False

        with open(database, 'rb') as f:
            header = f.read(100)

        return header[:16] == b'SQLite format 3\x00'

    url = copy(make_url(url))
    if hasattr(url, "_replace"):
        database = url.database
        url = url._replace(database=None)
    else:
        database, url.database = url.database, None

    engine = sa.create_engine(url)

    if engine.dialect.name == 'postgresql':
        text = "SELECT 1 FROM pg_database WHERE datname='%s'" % database
        return bool(get_scalar_result(engine, text))

    elif engine.dialect.name == 'mysql':
        text = ("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA "
                "WHERE SCHEMA_NAME = '%s'" % database)
        return bool(get_scalar_result(engine, text))

    elif engine.dialect.name == 'sqlite':
        if database:
            return database == ':memory:' or sqlite_file_exists(database)
        else:
            # The default SQLAlchemy database is in memory,
            # and :memory is not required, thus we should support that use-case
            return True

    else:
        engine.dispose()
        engine = None
        text = 'SELECT 1'
        try:
            if hasattr(url, "_replace"):
                url = url._replace(database=database)
            else:
                url.database = database

            engine = sa.create_engine(url)
            result = engine.execute(text)
            result.close()
            return True

        except (ProgrammingError, OperationalError):
            return False
        finally:
            if engine is not None:
                engine.dispose()

def get_bind(obj):
    """
    Return the bind for given SQLAlchemy Engine / Connection / declarative
    model object.
    :param obj: SQLAlchemy Engine / Connection / declarative model object
    ::
        from sqlalchemy_utils import get_bind
        get_bind(session)  # Connection object
        get_bind(user)
    """
    if hasattr(obj, 'bind'):
        conn = obj.bind
    else:
        try:
            conn = object_session(obj).bind
        except UnmappedInstanceError:
            conn = obj

    if not hasattr(conn, 'execute'):
        raise TypeError(
            'This method accepts only Session, Engine, Connection and '
            'declarative model objects.'
        )
    return conn

def quote(mixed, ident):
    """
    Conditionally quote an identifier.
    ::
        from sqlalchemy_utils import quote
        engine = create_engine('sqlite:///:memory:')
        quote(engine, 'order')
        # '"order"'
        quote(engine, 'some_other_identifier')
        # 'some_other_identifier'
    :param mixed: SQLAlchemy Session / Connection / Engine / Dialect object.
    :param ident: identifier to conditionally quote
    """
    if isinstance(mixed, Dialect):
        dialect = mixed
    else:
        dialect = get_bind(mixed).dialect
    return dialect.preparer(dialect).quote(ident)

def drop_database(url):
    """Issue the appropriate DROP DATABASE statement.
    :param url: A SQLAlchemy engine URL.
    Works similar to the :ref:`create_database` method in that both url text
    and a constructed url are accepted. ::
        drop_database('postgresql://postgres@localhost/name')
        drop_database(engine.url)
    """

    url = copy(make_url(url))

    database = url.database

    if url.drivername.startswith('postgres'):
        if hasattr(url, "set"):
            url = url.set(database='postgres')
        else:
            url.database = 'postgres'

    elif url.drivername.startswith('mssql'):
        if hasattr(url, "set"):
            url = url.set(database='master')
        else:
            url.database = 'master'

    elif not url.drivername.startswith('sqlite'):
        if hasattr(url, "_replace"):
            url = url._replace(database=None)
        else:
            url.database = None

    if url.drivername == 'mssql+pyodbc':
        engine = sa.create_engine(url, connect_args={'autocommit': True})
    elif url.drivername == 'postgresql+pg8000':
        engine = sa.create_engine(url, isolation_level='AUTOCOMMIT')
    else:
        engine = sa.create_engine(url)
    conn_resource = None

    if engine.dialect.name == 'sqlite' and database != ':memory:':
        if database:
            os.remove(database)

    elif (
                engine.dialect.name == 'postgresql' and
                engine.driver in {'psycopg2', 'psycopg2cffi'}
    ):
        if engine.driver == 'psycopg2':
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            connection = engine.connect()
            connection.connection.set_isolation_level(
                ISOLATION_LEVEL_AUTOCOMMIT
            )
        else:
            connection = engine.connect()
            connection.connection.set_session(autocommit=True)

        # Disconnect all users from the database we are dropping.
        version = connection.dialect.server_version_info
        pid_column = (
            'pid' if (version >= (9, 2)) else 'procpid'
        )
        text = '''
        SELECT pg_terminate_backend(pg_stat_activity.%(pid_column)s)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '%(database)s'
          AND %(pid_column)s <> pg_backend_pid();
        ''' % {'pid_column': pid_column, 'database': database}
        connection.execute(text)

        # Drop the database.
        text = 'DROP DATABASE {0}'.format(quote(connection, database))
        connection.execute(text)
        conn_resource = connection
    else:
        text = 'DROP DATABASE {0}'.format(quote(engine, database))
        conn_resource = engine.execute(text)

    if conn_resource is not None:
        conn_resource.close()
    engine.dispose()
