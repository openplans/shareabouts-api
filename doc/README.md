Setting up a Hey Duwamish API instance
======================================
Hey Duwamish requires python2.6 or greater (and PostgreSQL 9.1 and development libraries by default to build).

What's here
------------

This package contains the Shareabouts API web service,
which is a Django web application providing:

* A RESTful web service
* A management user interface, at /manage
* The basic Django admin UI, for low-level superuser tasks, at /admin

The Hey Duwamish web application JavaScript and related files are
*not* part of this package. [You'll need to install that separately](https://github.com/openplans/shareabouts/).

For more about the parts of Shareabouts,
see [the architecture documentation](ARCHITECTURE.md).

Database
--------

The Shareabouts REST API requires GeoDjango.  To install GeoDjango on your
platform, see https://docs.djangoproject.com/en/dev/ref/contrib/gis/install/#platform-specific-instructions.
For example, to install on Debian/Ubuntu, perform the following:

    sudo apt-get install postgresql-9.3 postgresql-9.3-postgis-2.1 postgresql-server-dev-9.3 python-psycopg2 binutils

Create a development database for the Shareabouts data store.

    sudo su postgres

For PostGIS 2.0:

    createdb shareabouts_v2
    psql -U postgres -d shareabouts_v2
    # inside the postgres CLI:
    # execute the '\password' psql command for set the password for the 'postgres' user:
    \password postgres
    # Enter a db password, noting that 'postgres' is the password in our template 'src/project/local_settings.py.template'
    Enter new password: <enter your password>
    Enter it again: <enter your password again>
    CREATE EXTENSION postgis;
    \q

To enable your database settings, go to the `src` folder and create a new hidden text file called `.env` and your information:

    PASS=<enter your password here>

We have a configuration with default settings that will load automatically. If you want to override any of the default database settings, add them to the `.env` file as follows:

    USERNAME=<default is 'postgres'>
    HOST=<default is 'localhost'>
    PORT=<default is '5432'>

Then bootstrap the development database using the usual Django command:

    src/manage.py migrate

Local setup
------------

Install `pip` and `virtualenv`, if not already installed.  These will keep your
requirements isolated from the rest of your machine.

    sudo apt-get install python-pip python-dev build-essential
    sudo pip install --upgrade pip
    sudo pip install --upgrade virtualenv

For older versions of ubuntu:

    sudo easy_install pip
    sudo pip install virtualenv

Create a new virtual environment inside of the repository folder, and install
the project requirements:

    virtualenv env
    source env/bin/activate
    pip install -r requirements.txt

(May have to first address Database section above, as `pip install -r
requirements.txt` may fail looking for `pg_config`.)


NOTE: If you run in to trouble with gevent, you can safely comment it out of
the requirements.txt file.  It is not needed for local development.  To comment
it out, just add a hash to the beginning of the line for `gevent`.

To run the development server:

    src/manage.py runserver 8001

This will start the service at http://localhost:8001/ .

If you don't specify a port, the server will start on port 8000.
We recommend getting in the habit of using port 8001 so you can
work with the sa-web front end application on the same development
host, and run that one on port 8000.

NOTE: If you're new to programming with virtual environments, be sure to remember
to activate your virtual environment every time you start a new terminal session.

    source env/bin/activate

Accessing the Management UI
----------------------------

To generate an API key to connect a web app with your locally deployed API, execute the following:

    ./src/manage.py createsuperuser

Create a username and password, then access the admin panel as follows (assuming that we've deployed to localhost 8001):

    http://localhost:8001/admin

Then create a dataset and API key. We can load these into our web-app as `SITE_URL` and `SITE_KEY` variables, which will connect our front end app to the API.

Running the Shareabouts Web Application
-----------------------------------------

For local development, you will probably also want to install and run [the
front-end mapping application](https://github.com/smartercleanup/duwamish/).


Deployment
-------------

See [the deployment docs](DEPLOY.md).


Testing
--------

To run the tests, run this command:

  src/manage.py test
