###########################################################
# Dockerfile to build Python WSGI Application Containers
# Based on Ubuntu
############################################################

# Set the base image to Ubuntu
FROM ubuntu

# File Author / Maintainer
MAINTAINER Luke Swart <luke@smartercleanup.org>

# Update the sources list
RUN apt-get update

# Install basic applications
RUN apt-get install -y tar git curl wget dialog net-tools build-essential gettext

# Install Python and Basic Python Tools
RUN apt-get install -y python-dev python-distribute python-pip

# Install Postgres/PostGIS dependencies:
RUN apt-get install -y postgresql-9.3 postgresql-9.3-postgis-2.1 postgresql-server-dev-9.3 python-psycopg2 postgresql libpq-dev

# If you want to deploy from an online host git repository, you can use the following command to clone:
RUN git clone https://github.com/smartercleanup/duwamish-api.git && cd duwamish-api && git checkout docker-deploy && cd -

# Get pip to download and install requirements:
RUN pip install -r /duwamish-api/requirements.txt

# Expose ports
EXPOSE 8010

# Set the default directory where CMD will execute
WORKDIR /duwamish-api/src
RUN ln -s staticfiles static
VOLUME /duwamish-api/static

# Set the default command to execute    
# when creating a new container
# i.e. using CherryPy to serve the application
# CMD python server.py
CMD gunicorn wsgi:application -w 3 -b 0.0.0.0:8010

