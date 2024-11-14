#!/bin/bash

OPTS=
CMD=
PARAMS=
CFG=/etc/opensips-cli.cfg

echo "[default]" > "$CFG"

while [[ $# -gt 0 ]]; do
	case "$1" in
	-o|--option)
		shift
		P=$(cut -d'=' -f1 <<<"$1")
		V=$(cut -d'=' -f2- <<<"$1")
		echo "$P: $V" >> "$CFG"
		;;
	*)
		if [ -z "$CMD" ]; then
			CMD="$1"
		else
			PARAMS="${PARAMS} ${1}"
		fi
		;;
	esac
	shift
done

if [[ $CMD == *.py ]]; then
	TOOL=python3
elif [[ $CMD == *.sh ]]; then
	TOOL=bash
else
	TOOL=opensips-cli
fi

exec $TOOL $CMD $PARAMS
