#!/bin/sh

# Add Postgres repositories
sudo apt-get install wget ca-certificates
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" >> /etc/apt/sources.list.d/pgdg.list'

sudo apt-get update

# libevent development files are required for gevent
echo
echo "** Updating libevent"
sudo apt-get install libevent-dev -y

# Install GeoDjango dependencies -- see
# https://docs.djangoproject.com/en/dev/ref/contrib/gis/install/#ubuntu
echo
echo "** Installing system-level project dependencies"
sudo apt-get install -y binutils gdal-bin libgdal-dev libproj-dev \
     postgresql postgresql-contrib postgis

# Install the python requirements
echo
echo "** Installing Python requirements"
sudo pip install -r requirements.txt

# ... and this, optional testing stuff
sudo pip install coverage

# Initialize the database
echo
echo "** Setting up the test database"
sudo -u postgres psql <<EOF
    CREATE USER shareabouts WITH PASSWORD 'shareabouts';
    CREATE DATABASE shareabouts;
    GRANT ALL ON DATABASE shareabouts TO shareabouts;
    ALTER USER shareabouts SUPERUSER;
EOF

sudo -u postgres psql -d shareabouts -c "CREATE EXTENSION postgis;"

# Initialize the project settings
cp src/project/local_settings.py.template src/project/local_settings.py
