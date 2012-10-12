#!/bin/sh

# This script is courtesy of the very useful DotCloud docs:
#   http://docs.dotcloud.com/0.4/guides/backups/
# Our streamlined docs can be found at doc/BACKUP.md. The only modification to
# this script is the '-c' flag on line 31 for simpler restoring.
# Love, OpenPlans

# Syntax:
# backup.sh <what> <how> <where> [whereexactly]
# <what> indicates what you want to backup: mysql, pgsql, riak, data.
# <how> indicates the backup method: ssh, ftp, s3.
# <where> is a <user[:password]@host>.
# [whereexactly] is an optional path on the <where> target, when applicable.
set -e
TAG="$HOSTNAME_$(TZ=UTC date +%Y-%m-%d_%H:%M:%S_UTC)"

[ "$3" ] || {
	echo "Please specify what to backup, how, and where."
	exit 1
}


case "$1" in
	mysql)
		FILENAME="$TAG.sql.gz"
		FILEPATH="/tmp/$FILENAME"
		mysqldump --all-databases | gzip > "$FILEPATH"
		;;
	pgsql)
		FILENAME="$TAG.sql.gz"
		FILEPATH="/tmp/$FILENAME"
		pg_dumpall -c | gzip > "$FILEPATH"
		;;
	riak)
		FILENAME="$TAG.bitcask.tar.gz"
		FILEPATH="/tmp/$FILENAME"
		tar -czf "$FILEPATH" /var/lib/riak
		;;
	data)
		FILENAME="$TAG.data.tar.gz"
		FILEPATH="/tmp/$FILENAME"
		tar -C "$HOME" -czf "$FILEPATH" "data"
		;;
	*)
		echo "Sorry, I don't know how to backup $1."
		exit 1
		;;
esac

if [ "$4" ]
then
	DEST="$4/$FILENAME"
else
	DEST="$FILENAME"
fi

case "$2" in
	ssh)
		scp -q -o BatchMode=yes "$FILEPATH" "$3:$DEST"
		;;
	ftp)
		curl -sST "$FILEPATH" "ftp://$3/$DEST"
		;;
	s3)
		s3cmd put "$FILEPATH" "s3://$3/$DEST"
		;;
	s3multi)
		split --numeric-suffixes --bytes=4G "$FILEPATH" "$FILEPATH".
		s3cmd put "$FILEPATH".?? "s3://$3/$DEST/"
		;;
	*)
		echo "Sorry, transfer method $2 is not supported."
		exit 1
esac

SIZE="$(stat --printf %s "$FILEPATH")"
echo "Backup $TAG completed. Its (compressed) size is $SIZE bytes."
rm -f "$FILEPATH"