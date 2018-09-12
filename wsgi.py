"""
WSGI config for project project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""
import os
import sys
from os.path import abspath, join
import subprocess

CURR_DIR = os.path.dirname(__file__)
sys.path.append(os.path.join(CURR_DIR, 'src'))
sys.path.append(abspath(join(CURR_DIR, 'libs', 'django-rest-framework-0.4')))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

subprocess.call("python src/manage.py collectstatic --noinput", shell=True)
# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Send errors to Sentry
from raven.contrib.django.raven_compat.middleware.wsgi import Sentry
application = Sentry(application)

from dj_static import Cling
application = Cling(application)

# from .src.project.twinkie import ExpiresMiddleware
# application = ExpiresMiddleware(application, {
#     'application/javascript': 365*24*60*60,
#     'text/css':               365*24*60*60,
#     'image/png':              365*24*60*60,
# })
