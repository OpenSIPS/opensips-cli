#!/bin/bash
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

CLI_CFG=/tmp/.__cli.cfg
DB_NAME=_opensips_cli_test

MYSQL_URL=mysql://opensips:opensipsrw@localhost
PGSQL_URL=postgres://opensips:opensipsrw@localhost

TESTS=(
  test_mysql_drop_1_prompt
  test_mysql_drop_0_prompts
  test_mysql_create_0_prompts

  test_pgsql_drop_1_prompt
  test_pgsql_drop_0_prompts
  test_pgsql_create_0_prompts
)


test_mysql_drop_1_prompt() { test_db_drop_1_prompt $MYSQL_URL; }
test_mysql_drop_0_prompts() { test_db_drop_0_prompts $MYSQL_URL; }
test_mysql_create_0_prompts() { test_db_create_0_prompts $MYSQL_URL; }

test_pgsql_drop_1_prompt() { test_db_drop_1_prompt $PGSQL_URL; }
test_pgsql_drop_0_prompts() { test_db_drop_0_prompts $PGSQL_URL; }
test_pgsql_create_0_prompts() { test_db_create_0_prompts $PGSQL_URL; }


test_db_drop_1_prompt() {
  create_db $DB_NAME $1

  cat >$CLI_CFG <<EOF
[default]
log_level: ERROR
database_admin_url: $1
EOF

  opensips-cli --config $CLI_CFG -x database drop $DB_NAME < <(cat <<EOF
y
EOF
) &>/dev/null
}


test_db_drop_0_prompts() {
  create_db $DB_NAME $1

  cat >$CLI_CFG <<EOF
[default]
log_level: ERROR
database_admin_url: $1
database_force_drop: false
EOF
  opensips-cli --config $CLI_CFG -x database drop $DB_NAME # NOP, no delete

  cat >$CLI_CFG <<EOF
[default]
log_level: ERROR
database_admin_url: $1
database_force_drop: true
EOF
  opensips-cli --config $CLI_CFG -x database drop $DB_NAME
}


test_db_create_0_prompts() {
  drop_db $DB_NAME $1

  cat >$CLI_CFG <<EOF
[default]
log_level: ERROR
database_admin_url: $1
database_modules: dialog
EOF

  # create
  opensips-cli --config $CLI_CFG -x database create $DB_NAME &>/dev/null

  drop_db $DB_NAME $1
}


create_db() {
  cat >$CLI_CFG <<EOF
[default]
log_level: ERROR
database_admin_url: $2
database_modules: dialog
EOF

  opensips-cli --config $CLI_CFG -x database create $1 &>/dev/null
}

drop_db() {
  cat >$CLI_CFG <<EOF
[default]
log_level: ERROR
database_admin_url: $2
database_force_drop: true
EOF

  set +e
  opensips-cli --config $CLI_CFG -x database drop $1 &>/dev/null
  set -e
}
