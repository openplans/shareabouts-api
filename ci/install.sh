#!/bin/sh

# libevent development files are required for gevent
echo
echo "** Updating libevent"
sudo apt-get install libevent-dev -y

# Install GeoDjango dependencies -- see
# https://docs.djangoproject.com/en/dev/ref/contrib/gis/install/#ubuntu
echo
echo "** Installing system-level project dependencies"
sudo apt-get install -y binutils gdal-bin libgdal-dev libproj-dev

# Install the python requirements
echo
echo "** Installing Python requirements"
sudo pip install -r requirements.txt

# ... and this, optional testing stuff
sudo pip install coverage

# Initialize the database
echo
echo "** Setting up the test database"
psql -U postgres <<EOF
    CREATE USER shareabouts WITH PASSWORD 'shareabouts';
    CREATE DATABASE shareabouts;
    GRANT ALL ON DATABASE shareabouts TO shareabouts;
    ALTER USER shareabouts SUPERUSER;
EOF

psql -U postgres -d shareabouts -c "CREATE EXTENSION postgis;"

# Initialize the project settings
cp src/project/local_settings.py.template src/project/local_settings.py
