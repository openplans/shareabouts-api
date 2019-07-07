#!/bin/sh

# Install the python requirements
echo
echo "** Installing Python requirements"
pip install -r requirements.txt

# ... and this, optional testing stuff
pip install coverage

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
