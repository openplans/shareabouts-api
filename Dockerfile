###########################################################
# Dockerfile to build Python WSGI Application Containers
# Based on Ubuntu
############################################################

# Set the base image to Ubuntu
FROM buildpack-deps:jessie

# File Author / Maintainer
MAINTAINER Luke Swart <luke@smartercleanup.org>

# Update the sources list
RUN apt-get update

# Install basic applications
RUN apt-get install -y tar git curl wget dialog net-tools build-essential gettext

# Install Python and Basic Python Tools
RUN apt-get install -y python-dev python-distribute python-pip

# Install Postgres/PostGIS dependencies:
RUN apt-get install -y python-psycopg2 postgresql libpq-dev postgresql-9.4-postgis-2.1 postgis postgresql-9.4

# If you want to deploy from an online host git repository, you can use the following command to clone:
RUN git clone https://github.com/smartercleanup/api.git && cd api && git checkout docker-deploy && cd -
# local testing:
# ADD . api

# Get pip to download and install requirements:
RUN pip install -r /api/requirements.txt

# Expose ports
EXPOSE 8010

# Set the default directory where CMD will execute
WORKDIR /api

RUN mkdir static
VOLUME /api/static

# Set the default command to execute
# when creating a new container
# ex:
# CMD python server.py
CMD sh -c "python src/manage.py collectstatic --noinput && gunicorn wsgi:application -w 3 -b 0.0.0.0:8010"
