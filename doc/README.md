From 0 to a Shareabouts API instance in about an hour
======================================
Shareabouts requires python2.6 or greater (and PostgreSQL 9.1 and development libraries by default to build). **We strongly recommend that you use Python 3.6+**


What's here
------------

This package contains the Shareabouts API web service,
which is a Django web application providing:

* A RESTful web service
* A management user interface, at /manage
* The basic Django admin UI, for low-level superuser tasks, at /admin

The Shareabouts web application JavaScript and related files are
*not* part of this package. [You'll need to install that separately](https://github.com/openplans/shareabouts/).

For more about the parts of Shareabouts,
see [the architecture documentation](ARCHITECTURE.md).


Database
--------

The Shareabouts REST API requires GeoDjango.  To install GeoDjango on your
platform, see https://docs.djangoproject.com/en/dev/ref/contrib/gis/install/#platform-specific-instructions.

Create a development database for the Shareabouts data store. For most users installing PostgreSQL for the first time, you will be using PostGIS 2.0:

    sudo -u postgres psql -c "create user $(whoami) with superuser;"
    createdb shareabouts_v2
    psql -d shareabouts_v2 -c 'CREATE EXTENSION postgis;'

If you know you have PostGIS 1.5 or earlier, run this instead:

    createdb -T template_postgis shareabouts_v2


Local setup
------------

Create a new virtual environment inside of the repository folder, and install
the project requirements:

    python3 -m venv env
    source env/bin/activate
    pip install -r requirements.txt

NOTE: If you run in to trouble with gevent, you can safely comment it out of
the requirements.txt file.  It is not needed for local development.  To comment
it out, just add a hash to the beginning of the line for `gevent`. Same for `psycogreen`.

Copy the file `.env.template` to `.env` and fill in the credentials for connecting to your development database. This file will not be checked in to the repository. Remember to replace the `YOUR_USERNAME_HERE` in `.env` with your actual username. you can get your username by running `whoami` on the command line.

Install `honcho`, which we use to pass variables into the server's environment.

    sudo pip install honcho

Then bootstrap the development database tables using `honcho` and the usual Django command:

    honcho run src/manage.py migrate

Create an admin user for logging in to your local API's admin interface:

    honcho run src/manage.py createsuperuser

To run the development server:

    honcho run src/manage.py runserver 8001

This will start the service at http://localhost:8001/admin .

If you don't specify a port, the server will start on port 8000.
We recommend getting in the habit of using port 8001 so you can
work with the sa-web front end application on the same development
host, and run that one on port 8000.

NOTE: If you're new to programming with virtual environments, be sure to
remember to activate your virtual environment every time you start a new
terminal session.

    source env/bin/activate


Creating your first dataset
---------------------------

1. Each map instance stores the surveys submitted through the interface in a "dataset". Here we will create a dataset to use for testing and development purposes. With your API server running, browse to http://localhost:8001/admin. Log in with your superuser username and password. Scroll down to click on **Data sets** under the *SA_API_V2* heading.

   Then, in the top-right of the screen, click button labeled **ADD DATA SET**.

2. On the next screen, click the magnifying glass next to the *Owner* box. Click the username of your superuser in the window that pops up. Next, enter a *Display name* for the dataset -- something like "My Test Dataset". The *Slug* should populate automatically. Scroll all the way to the bottom of the page and click the **Save and continue editing** button.

3. Now create an API key for the dataset by clicking **Add another Api key** under the *API KEYS* section. Then, scroll to the bottom of the page and click **Save and continue editing** again. Your dataset is now ready to receive submissions.

If you want to point a Shareabouts client at your new dataset, copy the *Key* from your API key, find the `SHAREABOUTS` dictionary in your client `local_settings.py` file and change the `DATASET_KEY` the key that your copied.

Next, copy the _link address_ of the "Api path" from your dataset admin page, and find the `DATASET_ROOT` in the client `local_settings.py`. Place the API path link address value there.

Now, start the client application _on a different port than the API server_. With both servers running, open http://localhost:8000 in your browser. Congratulations on your first complete setup!


Running the Shareabouts Web Application
-----------------------------------------

For local development, you will probably also want to install and run [the
front-end mapping application](https://github.com/openplans/shareabouts/).


Deployment
-------------

See [the deployment docs](DEPLOY.md).


Testing
--------

To run the tests, run this command:

  src/manage.py test

