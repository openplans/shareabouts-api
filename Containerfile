FROM ubuntu:24.04

# Install Python & GeoDjango dependencies
RUN apt update && \
    apt install -y \
    libpq-dev \
    libproj-dev \
    gdal-bin \
    python3 \
    python3-pip \
    python3-venv && \
    apt clean

# Create a virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy the application code to the container
COPY src /app
COPY pytest.ini /app/pytest.ini
WORKDIR /app

# Run collectstatic to gather static files
# We pass dummy values for REDIS_URL and SECRET_KEY to ensure settings.py loads without error
RUN REDIS_URL="redis://dummy:6379/0" \
    SECRET_KEY="dummy" \
    ALLOWED_HOSTS="*" \
    python3 manage.py collectstatic --noinput

# Copy gunicorn config
COPY gunicorn.conf.py /app/gunicorn.conf.py

# Expose the port the app runs on
EXPOSE 8000

# Default command
CMD ["sh", "-c", "gunicorn project.wsgi --pythonpath src --workers 3 --config gunicorn.conf.py --bind 0.0.0.0:${PORT:-8000}"]


