These instructions apply only to the "Shareabouts API" application.
If you are also building and installing the Shareabouts web front-end,
it has its own documentation.

Deploying to DotCloud
---------------------

At OpenPlans, we have been deploying Shareabouts to DotCloud internally, so many
of the files necessary are already in the repository.

* First, create a new dotcloud application from the contents of the `master` branch:

        dotcloud create <instance name>

* Push the code to DotCloud.  This will take several minutes the first time.

        dotcloud push -A <instance name> --git

  Note you should first either push all your changes to your master
  repository (eg. github or whatever you're using for version
  control);  otherwise you must use the dotcloud push --all option.

  For more options, see `dotcloud push --help`

* If you wish to use attachments, you'll need to set up your Django storage
  settings. By default, Django uses a FileSystemStorage backend, which stores
  files on a local file system. If you wish to use this default, then set your
  MEDIA_ROOT and MEDIA_URL in local_settings.py (see Django's documentation on
  [The built-in filesystem storage class](https://docs.djangoproject.com/en/1.4/topics/files/#the-built-in-filesystem-storage-class)).

  You can alternatively use Amazon S3 to store and serve your uploaded media.
  To use this option, on DotCloud, set the following variables:

        dotcloud env -A <instance name> set \
          SHAREABOUTS_AWS_KEY=<AWS access key id>\
          SHAREABOUTS_AWS_SECRET=<AWS secret access key>\
          SHAREABOUTS_AWS_BUCKET=<S3 bucket name>

  The Shareabouts API server uses *django-storages* to for media storage. Refer
  to their [documentation](http://django-storages.readthedocs.org/) for more
  information.

* On first deploy only: You'll want to create a superuser to get in to
  the management UI:

        dotcloud run -A <instance name> www current/src/manage.py createsuperuser


Deploying to Heroku
-------------------

0. Clone the shareabouts-api repository
1. Create a Heroku app
2. Add addons

    "heroku-postgresql:standard-0"
    "rediscloud:500"
    "newrelic"
    "adept-scale"
    "pgbackups:auto-month"

3. Promote the new database
4. Set environment variables

        BUILDPACK_URL:               https://github.com/heroku/heroku-buildpack-multi.git
        DEBUG:                       False
        NEW_RELIC_APP_NAME:          Shareabouts API (Production, Heroku)
        REDIS_URL:                   [Set to REDISCLOUD_URL or OPENREDIS_URL]
        SHAREABOUTS_ADMIN_EMAIL:     admin@example.com
        SHAREABOUTS_AWS_BUCKET:      shareabouts_attachments
        SHAREABOUTS_AWS_KEY:         ABCDEFGHIJKL12MNO3PQ
        SHAREABOUTS_AWS_SECRET:      abcDEfGhi+1JKlMnOPqr2sT34UVWXy+zaBcdEFgH
        SHAREABOUTS_FACEBOOK_KEY:    123456789012345
        SHAREABOUTS_FACEBOOK_SECRET: a1234bc56d78ef901g234h567ijklmn8
        SHAREABOUTS_TWITTER_KEY:     aB1cd2EFGhi3JK4lMn5oP
        SHAREABOUTS_TWITTER_SECRET:  ABcDE1FgHIjKlmN2o3pQrsTUVW4X5Cy67zabCdEFGHi
        WORKERS: 4
        BUILD_WITH_GEO_LIBRARIES: 1

5. Connect the app with the repository (add a git remote)
6. Push to Heroku
7. Run database migrations (or copy the database from elsewhere)
