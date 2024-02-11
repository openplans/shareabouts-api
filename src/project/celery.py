
from __future__ import absolute_import, unicode_literals
import os
import sys
from os.path import abspath, join
from celery import Celery

CURR_DIR = os.path.dirname(__file__)
sys.path.append(abspath(join(CURR_DIR, '../../libs', 'django-rest-framework-0.4')))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

app = Celery('project_wide')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(('Request: {0!r}'.format(self.request)))
