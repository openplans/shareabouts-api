web: newrelic-admin run-program gunicorn project.wsgi --pythonpath src --workers $WORKERS --config gunicorn.conf.py
worker: src/manage.py celery worker