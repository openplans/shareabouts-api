#!/bin/bash

python src/manage.py collectstatic --noinput
gunicorn wsgi:application -w 3 -b 0.0.0.0:8010 --log-level=debug

