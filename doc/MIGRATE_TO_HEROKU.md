Migrating the API from DotCloud to Heroku
=========================================

Here are the rough steps we took:

1.  Created a heroku app.

        heroku apps:create

2.  Copied Shareabouts environment variables from DotCloud.

        dotcloud env list 
        heroku config:set ...

3.  Pushed.

        git push heroku master

4.  Added a database addon -- must be one that supports PostGIS.

        heroku addons:add heroku-postgresql:standard-yanari

5.  Promoted the database.

        heroku pg:promote HEROKU_POSTGRESQL_RED_URL

6.  Added backup/restore.

        heroku addons:add pgbackups:auto-month

7.  Copied the DotCloud database to Heroku.

        export DB_PASS_KEY="DOTCLOUD_DB_SQL_PASSWORD="
        export DB_PASS_SETTING=$(dotcloud --application shareaboutsapi env list | grep "$DB_PASS_KEY")
        export DB_PASS_INDEX=${#DB_PASS_KEY}

        heroku pg:reset DATABASE_URL
        heroku pg:psql CREATE EXTENSION postgis;

        dotcloud -A shareaboutsapi run db \
            "PGPASSWORD=${DB_PASS_SETTING:$DB_PASS_INDEX} \
            pg_dump --no-privileges --no-owner --blobs \
            --format=plain -h localhost -U root shareabouts" \
            > shareaboutsapi.$(date --iso-8601).dump

        cat shareaboutsapi.$(date --iso-8601).dump | heroku pg:psql DATABASE_URL

8.  Note that you could even skip the file creation and the cat command, and
    pipe the pg_dump output directly into pg:psql.  If you want to explicitly
    convert the contents to PostGIS 2, use --format=custom instead, and use the
    fancy script that Aaron knows about.

9.  Provisioned a RedisCloud addon.

        heroku addons:add rediscloud

10. Copied the Redis URL for RedisCloud.

        REDISCLOUD_URL = $(heroku config:get RESISCLOUD_URL)
        heroku config:set REDIS_URL=$REDISCLOUD_URL

11. Sent the static assets to S3.

        heroku run python src/manage.py collectstatic

