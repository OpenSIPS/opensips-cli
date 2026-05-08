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
## THIS SOFTWARE IS PROVIDED "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
## INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
## FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
## COPYRIGHT HOLDER BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
## EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
## PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
## OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
## WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
## OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
## ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
##
## Adapted from https://github.com/kvesteri/sqlalchemy-utils
## Updated for SQLAlchemy 1.4/2.0 compatibility (engine.execute removed).
## Please check LICENSE

from copy import copy

import os
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError

try:
    from sqlalchemy import make_url
except ImportError:
    from sqlalchemy.engine.url import make_url


def _get_scalar(engine, sql):
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        value = result.scalar()
    engine.dispose()
    return value


def database_exists(url):
    """Check if a database exists."""

    def sqlite_file_exists(database):
        if not os.path.isfile(database) or os.path.getsize(database) < 100:
            return False
        with open(database, 'rb') as f:
            header = f.read(100)
        return header[:16] == b'SQLite format 3\x00'

    url = copy(make_url(url))
    try:
        database = url.database
        url = url.set(database=None)
    except AttributeError:
        database, url.database = url.database, None

    if url.get_dialect().name == 'sqlite':
        if database:
            return database == ':memory:' or sqlite_file_exists(database)
        return True

    # connecting without a database is unreliable: psycopg2 always requires
    # a target DB, and some PyMySQL versions ignore database=None — point at
    # a system DB that is always present instead
    if url.get_dialect().name == 'postgresql':
        try:
            url = url.set(database='postgres')
        except AttributeError:
            url.database = 'postgres'
    elif url.get_dialect().name == 'mysql':
        try:
            url = url.set(database='information_schema')
        except AttributeError:
            url.database = 'information_schema'

    engine = sa.create_engine(url, isolation_level='AUTOCOMMIT')

    if engine.dialect.name == 'postgresql':
        sql = "SELECT 1 FROM pg_database WHERE datname='%s'" % database
        return bool(_get_scalar(engine, sql))

    elif engine.dialect.name == 'mysql':
        sql = ("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA "
               "WHERE SCHEMA_NAME = '%s'" % database)
        return bool(_get_scalar(engine, sql))

    else:
        try:
            url = copy(make_url(str(url)))
            try:
                url = url.set(database=database)
            except AttributeError:
                url.database = database
            engine2 = sa.create_engine(url)
            with engine2.connect() as conn:
                conn.execute(text('SELECT 1'))
            engine2.dispose()
            return True
        except (ProgrammingError, OperationalError):
            return False


def drop_database(url):
    """Issue the appropriate DROP DATABASE statement."""

    url = copy(make_url(url))
    database = url.database

    if url.drivername.startswith('postgres'):
        try:
            url = url.set(database='postgres')
        except AttributeError:
            url.database = 'postgres'
    elif url.drivername.startswith('mssql'):
        try:
            url = url.set(database='master')
        except AttributeError:
            url.database = 'master'
    elif url.drivername.startswith('mysql'):
        try:
            url = url.set(database='information_schema')
        except AttributeError:
            url.database = 'information_schema'
    elif not url.drivername.startswith('sqlite'):
        try:
            url = url.set(database=None)
        except AttributeError:
            url.database = None

    engine = sa.create_engine(url, isolation_level='AUTOCOMMIT')

    if engine.dialect.name == 'sqlite' and database != ':memory:':
        if database:
            os.remove(database)
        engine.dispose()
        return

    with engine.connect() as conn:
        if engine.dialect.name == 'postgresql':
            pid_column = 'pid'
            terminate_sql = """
            SELECT pg_terminate_backend(pg_stat_activity.%(pid)s)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '%(db)s'
              AND %(pid)s <> pg_backend_pid()
            """ % {'pid': pid_column, 'db': database}
            conn.execute(text(terminate_sql))

        quoted = engine.dialect.preparer(engine.dialect).quote(database)
        conn.execute(text('DROP DATABASE {}'.format(quoted)))

    engine.dispose()
