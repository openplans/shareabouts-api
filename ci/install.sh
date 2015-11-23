#!/bin/sh

# libevent development files are required for gevent
sudo apt-get install libevent-dev

# Install GeoDjango dependencies -- see
# https://docs.djangoproject.com/en/dev/ref/contrib/gis/install/#ubuntu
sudo apt-get install binutils gdal-bin libproj-dev postgresql-9.1-postgis \
     postgresql-server-dev-9.1 python-psycopg2

# Install the python requirements
sudo pip install -r requirements.txt

# ... and this, optional testing stuff
sudo pip install coverage

# Initialize the database
psql -U postgres <<EOF
    CREATE USER shareabouts WITH PASSWORD 'shareabouts';
    CREATE DATABASE shareabouts;
    GRANT ALL ON DATABASE shareabouts TO shareabouts;
    ALTER USER shareabouts SUPERUSER;
EOF

psql -U postgres -d shareabouts -c "CREATE EXTENSION postgis;"

# Initialize the project settings
cp src/project/local_settings.py.template src/project/local_settings.py
