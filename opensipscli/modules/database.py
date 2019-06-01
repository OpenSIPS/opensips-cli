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
from opensipscli.db import osdb, osdbError

import os

DEFAULT_DB_NAME = "opensips"
DEFAULT_ROLE_NAME = "opensips"
DEFAULT_DB_TEMPLATE = "template1"
DEFAULT_ROLE_OPTIONS = [
	"NOCREATEDB",
	"NOCREATEROLE",
	"LOGIN",
	"REPLICATION"
]
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
	"""
	methods to handle database objects
	"""

	def __complete__(self, command, text, line, begidx, endidx):
		rule_commands = (
			'alter_role',
			'create_role',
			'drop_role',
			'get_role')

		if command in rule_commands:
			role_name = ['opensips', 'test']
			if not text:
				return role_name

		ret = [t for t in role_name if t.startswith(text)]

		return ret if ret else ['']

	def __exclude__(self):
		if cfg.exists("database_url"):
			db_url = cfg.get("database_url")
			return not osdb.has_dialect(osdb.get_dialect(db_url))
		else:
			return not osdb.has_sqlalchemy()

	def __get_methods__(self):
		return ['', 'add', 'alter_role', 'create', 'create_role', 'drop', 'drop_role', 'get_role']

	#def __invoke__(self, cmd, params=None):
	#    if cmd is None:
	#        return self.diagnosis_summary()
	#    if cmd == 'create_role':
	#        #if not params:
	#            #params = ['role_name', 'role_options']
	#            #params = ['opensips', 'NOCREATEDB NOCREATEROLE LOGIN REPLICATION']
	#        return self.do_create_role(params)
	#    if cmd == 'drop_role':
	#        return self.do_drop_role(params)
	#    if cmd == 'get_role':
	#        return self.do_get_role()

	def do_add(self, params):
		"""
		add a given table to the database (connection via URL)
		"""
		if len(params) < 1:
			logger.error("No module to add added")
			return -1
		module = params[0]

		db_url = cfg.read_param("database_url",
				"Please provide us the URL of the database")
		if db_url is None:
			print()
			logger.error("no URL specified: aborting!")
			return -1

		if len(params) < 2:
			db_name = cfg.read_param("database_name",
					"Please provide the database to add the module to",
					DEFAULT_DB_NAME)
		else:
			db_name = params[1]


		db = osdb(db_url, db_name)

		if not db.exists():
			logger.warning("database '{}' does not exist!".format(db_name))
			return -1

		db_schema = db.dialect
		schema_path = self.get_schema_path(db_schema)
		if schema_path is None:
			return -1

		module_file_path = os.path.join(schema_path,
				"{}-create.sql".format(module))
		if not os.path.isfile(module_file_path):
			logger.warning("cannot find OpenSIPS DB file: '{}'!".
				format(module_file_path))
			return -1

		db.use()
		try:
			db.create_module(module_file_path)
		except osdbError as ex:
			logger.error("cannot import: {}".format(ex))
			return -1

		db.destroy()
		logger.info("Module {} has been successfully added!".
			format(module))
		return 0

	def do_alter_role(self, params=None):
		"""
		alter role attributes (connect to given template database)
		"""

		db_url = cfg.read_param("database_url",
			"Please provide the database connection URL")
		if db_url is None:
			logger.error("no URL specified: aborting!")
			return -1

		db_template = cfg.read_param("database_template",
			"Please provide the database template name",
			DEFAULT_DB_TEMPLATE)
		if db_template is None:
			logger.error("no URL specified: aborting!")
			return -1

		db = osdb(db_url, db_template)

		if len(params) < 2:
			role_name = cfg.read_param("role_name",
				"Please provide the role name to alter",
				DEFAULT_ROLE_NAME)
			logger.debug("role_name: '%s'", role_name)
		else:
			role_name = params[0]

		if len(params) < 3:
			role_list = cfg.read_param("role_options",
				"Please adapt the role options to alter",
				DEFAULT_ROLE_OPTIONS)
			if len(role_list) > 0:
				role_options = ' '.join(role_list)
			else:
				role_options = ' '.join(DEFAULT_ROLE_OPTIONS)
			logger.debug("role_options: '%s'", role_options)
		else:
			role_options = params[1]

		if db.exists_role(role_name) is True:
			if db.alter_role(role_name, role_options) is False:
				logger.error("alter role '%s' didn't succeed", role_name)
				db.destroy()
		else:
			logger.warning("can't alter non existing role '{}'".format(role_name))

	def do_create(self, params=None):
		"""
		create a role (connect to given template database)
		"""

		db_url = cfg.read_param("database_url",
				"Please provide us the URL of the database")
		if db_url is None:
			print()
			logger.error("no URL specified: aborting!")
			return -1

		if params and len(params) > 0:
			db_name = params[0]
		else:
			db_name = cfg.read_param("database_name",
				"Please provide the database to create",
				DEFAULT_DB_NAME)

		db = osdb(db_url, db_name)

		# check to see if the database has already been created
		if db.exists():
			logger.warn("database '{}' already exists!".format(db_name))
			return -2
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

		db.create()
		if (db.exists_role()) is False:
			self.do_create_role(params)
		db.grant_db_options()
		db.use()

		for table_file in tables_files:
			try:
				db.create_module(table_file)
			except osdbError as ex:
				logger.error("cannot import: {}".format(ex))

		db.destroy()
		logger.info("The database has been successfully created.")
		return 0

	def do_create_role(self, params=None):
		"""
		create a given role (connection via URL)
		"""

		db_url = cfg.read_param("database_url",
			"Please provide the database connection URL")
		if db_url is None:
			logger.error("no URL specified: aborting!")
			return -1

		db_template = cfg.read_param("database_template",
			"Please provide the database template name",
			DEFAULT_DB_TEMPLATE)
		if db_template is None:
			logger.error("no URL specified: aborting!")
			return -1

		db = osdb(db_url, db_template)

		#logger.debug("params [%i]: '%s'", len(params), params)
		if len(params) < 1:
			role_name = cfg.read_param("role_name",
				"Please provide the role name to create",
				DEFAULT_ROLE_NAME)
		else:
			role_name = params[0]
		logger.debug("role_name: '%s'", role_name)

		if len(params) < 2:
			role_list = cfg.read_param("role_options",
				"Please assing the list of role options to create",
				DEFAULT_ROLE_OPTIONS)
			#if len(role_list) > 0:
			#    # needs to be a list ['option', 'option']
			#    role_options = role_list
			#else:
			role_options = ' '.join(role_list)
		else:
			role_options = params[1]
		logger.debug("role_options: '%s'", role_options)

		if len(params) < 3:
			role_password = 'opensipspw'
		logger.debug("role_password: '********'")

		if db.exists_role(role_name) is False:
			if db.create_role(role_name, role_options, role_password) is False:
				logger.error("creating role '%s' didn't succeed", role_name)
				db.destroy()
		else:
			logger.warning("role '{}' already exists. Please use 'alter_role'".format(role_name))
			return False

	def do_drop(self, params=None):
		"""
		drop a given database object (connection via URL)
		"""

		db_url = cfg.read_param("database_url",
				"Please provide us the URL of the database")
		if db_url is None:
			print()
			logger.error("no URL specified: aborting!")
			return -1

		if params and len(params) > 0:
			db_name = params[0]
		else:
			db_name = cfg.read_param("database_name",
					"Please provide the database to drop",
					DEFAULT_DB_NAME)

		db = osdb(db_url, db_name)

		# check to see if the database has already been created
		if db.exists():
			if cfg.read_param("database_force_drop",
					"Do you really want to drop the '{}' database".
						format(db_name),
					False, True):
				db.drop()
				if db.exists_role():
					if cfg.read_param("role_force_drop",
						"Do you really want to drop the '{}' role".
							format(db_name),
						False, True):
						self.do_drop_role(params)
			else:
				logger.info("database '{}' not dropped!".format(db_name))
		else:
			logger.warning("database '{}' does not exist!".format(db_name))

	def do_drop_role(self, params=None):
		"""
		drop a given role (connection to given template via URL)
		"""

		db_url = cfg.read_param("database_url",
				"Please provide us the URL of the database")
		if db_url is None:
			print()
			logger.error("no URL specified: aborting!")
			return -1

		if params and len(params) > 0:
			role_name = params[0]
		else:
			role_name = cfg.read_param("role_name",
					"Please provide the role name to drop",
					DEFAULT_ROLE_NAME)

		db_name = "template1"
		db = osdb(db_url, db_name)

		if db.exists_role(role_name) is True:
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

		db_url = cfg.read_param("database_url",
				"Please provide database connection URL")
		if db_url is None:
			logger.error("no URL specified: aborting!")
			return -1

		db_template = cfg.read_param("database_template",
			"Please provide the database template name",
			DEFAULT_DB_TEMPLATE)
		if db_template is None:
			logger.error("no URL specified: aborting!")
			return -1

		db = osdb(db_url, db_template)

		if len(params) < 1:
			role_name = cfg.read_param("role_name",
				"Please provide the role name to alter",
				DEFAULT_ROLE_NAME)
		else:
			role_name = params[0]

		logger.debug("role_name: '%s'", role_name)


		if db.exists_role(role_name) is True:
			if db.get_role(role_name) is False:
				logger.error("get role '%s' didn't succeed", role_name)
		else:
			logger.warning("can't get options of non existing role '{}'".format(role_name))


	def get_schema_path(self, db_schema):
		"""
		get the path defining the root path holding sqk schema template
		"""

		db_path = cfg.read_param("database_path",
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
