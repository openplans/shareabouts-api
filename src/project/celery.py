
from __future__ import absolute_import, unicode_literals
import os
import sys
from os.path import abspath, join

CURR_DIR = os.path.dirname(__file__)
sys.path.append(abspath(join(CURR_DIR, '../../libs', 'django-rest-framework-0.4')))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

from celery import Celery
app = Celery('project_wide')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
from django.conf import settings
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print(('Request: {0!r}'.format(self.request)))