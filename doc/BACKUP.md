Backup and restore your database on DotCloud
============================================
These docs will cover backing up your Shareabouts API database to Amazon S3. We
assume that you know how to setup an account on Amazon AWS and how to create a
S3 bucket for storing your backup files. If not, checkout these
[docs](http://aws.amazon.com/documentation/s3/).

If you prefer to backup to another location, the complete instructions for
backing up a database on DotCloud can be found
[here](http://docs.dotcloud.com/0.4/guides/backups/).

Backup
------

1. Setup your S3 bucket. You'll need the bucket name, access key, and secret
key handy.
2. Login to your service on DotCloud. It should be something like
`dotcloud ssh shareaboutsapi.db`
3. Copy our backup script (a slight modification of the DotCloud backup script).
`curl --output dotcloud_db_backup.sh https://raw.github.com/openplans/shareabouts-api/master/scripts/dotcloud_db_backup.sh`
4. Make your script executable `chmod +x dotcloud_db_backup.sh`
5. Run `s3cmd --configure` setup access to your S3 bucket. Enter your
`access key` and `secret key` here. The `Encryption password` and
`Path to GPG program` are optional if you prefer.
6. When it asks "Test access with supplied credentials?", enter `Y` to make
sure the configuration is correct.
7. Test the backup! `~/dotcloud_db_backup.sh pgsql s3 shareaboutsapi_backups`
where `shareaboutsapi_backups` is your bucket name.

Schedule Backups
----------------
Follow DotClouds instructions [here](http://docs.dotcloud.com/0.4/guides/backups/#schedule-the-backup-script-with-a-crontab)
for using `crontab` to schedule your backups and get confirmation emails.
Note that our script is called `dotcloud_db_backup.sh` not `backup.sh`.

Restore
-------

1. Get the backup file that you want from S3. Something like
`s3cmd get s3://shareaboutsapi_backups/2012-10-12_13:47:50_UTC.sql.gz` where
`shareaboutsapi_backups` is your bucket name and `2012-10-12_13:47:50_UTC.sql.gz`
is your backup file name.
2. Unzip your file. `gunzip 2012-10-12_13:47:50_UTC.sql.gz`
3. Restore your database `psql -f 2012-10-12_13:47:50_UTC.sql`

Note that this backup is "clean" and will drop your entire database and do a
full restore.
