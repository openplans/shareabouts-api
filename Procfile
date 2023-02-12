web: gunicorn project.wsgi --pythonpath src --workers $WORKERS --config gunicorn.conf.py
worker: celery --workdir=src --app=project worker
