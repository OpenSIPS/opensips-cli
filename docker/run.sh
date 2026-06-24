#!/bin/sh

CMD=
PARAMS=
CFG=/etc/opensips-cli.cfg

echo "[default]" > "$CFG"

while [ $# -gt 0 ]; do
	case "$1" in
	-o|--option)
		shift
		P=$(echo "$1" | cut -d'=' -f1)
		V=$(echo "$1" | cut -d'=' -f2-)
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

case "$CMD" in
*.py) TOOL=python3 ;;
*.sh) TOOL=sh ;;
*)    TOOL=opensips-cli ;;
esac

exec $TOOL $CMD $PARAMS
