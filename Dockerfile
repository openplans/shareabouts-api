FROM ubuntu:24.04

# Install Python & GeoDjango dependencies
RUN apt update && \
    apt install -y \
        libpq-dev \
        libproj-dev \
        gdal-bin \
        python3 \
        python3-pip && \
    apt clean

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt --break-system-packages

# Copy the application code to the container
COPY src /app
WORKDIR /app

# Run collectstatic to gather static files
RUN REDIS_URL="redis://temp_value/" \
    python3 manage.py collectstatic --noinput

# Expose the port the app runs on
COPY gunicorn.conf.py /app/gunicorn.conf.py
EXPOSE 8000
