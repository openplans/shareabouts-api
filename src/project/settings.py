from os import environ
import os

DEBUG = False
TEMPLATE_DEBUG = DEBUG
SHOW_DEBUG_TOOLBAR = DEBUG
DEBUG_TOOLBAR_PATCH_SETTINGS = False

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

USE_GEODB = (environ.get('USE_GEODB', 'True').lower() == 'true')
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis', # Add 'backends.postgis', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': environ.get('RDS_DB_NAME'),  # Or path to database file if using sqlite3.
        'USER': environ.get('RDS_USERNAME'), # Not used with sqlite3.
        'PASSWORD':  environ.get('RDS_PASSWORD'), # Not used with sqlite3.
        'HOST': environ.get('RDS_HOSTNAME'), # Set to empty string for localhost. Not used with sqlite3.
        'PORT': environ.get('RDS_PORT'),     # Set to empty string for default. Not used with sqlite3.
    }
}

###############################################################################
#
# Server Configuration
#

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']
SECRET_KEY = 'pbv(g=%7$$4rzvl88e24etn57-%n0uw-@y*=7ak422_3!zrc9+'
SITE_ID = 1

# How long to keep api cache values. Since the api will invalidate the cache
# automatically when appropriate, this can (and should) be set to something
# large.
API_CACHE_TIMEOUT = 3600  # an hour

# Where should the user be redirected to when they visit the root of the site?
ROOT_REDIRECT_TO = 'api-root'

###############################################################################
#
# Time Zones
#

TIME_ZONE = 'Universal'
USE_TZ = True

###############################################################################
#
# Internationalization and Localization
#

LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = True

###############################################################################
#
# Templates and Static Assets
#

MEDIA_ROOT = ''
MEDIA_URL = ''

STATIC_ROOT = '/opt/python/current/app/static'
STATIC_URL = '/static/'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
STATICFILES_DIRS = ()

#STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.staticfiles_storage'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)
TEMPLATE_DIRS = ()

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    'django.core.context_processors.request',
)

ATTACHMENT_STORAGE = 'django.core.files.storage.FileSystemStorage'

###############################################################################
#
# Django Rest Framework
#
REST_FRAMEWORK = {
    'PAGINATE_BY': 100,
    'PAGINATE_BY_PARAM': 'page_size'
}

###############################################################################
#
# Request/Response processing
#

WSGI_APPLICATION = 'project.wsgi.application'
ROOT_URLCONF = 'project.urls'

MIDDLEWARE_CLASSES = (
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'remote_client_user.middleware.RemoteClientMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'social.apps.django_app.middleware.SocialAuthExceptionMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'sa_api_v2.middleware.RequestTimeLogger',
    'sa_api_v2.middleware.UniversalP3PHeader',
)

# We only use the CORS Headers app for oauth. The Shareabouts API resources
# have their own base view that handles CORS headers.
CORS_URLS_REGEX = r'^/api/v\d+/users/oauth2/.*$'
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True


###############################################################################
#
# Pluggable Applications
#

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',

    # =================================
    # 3rd-party reusaple apps
    # =================================
    'rest_framework',
    'django_nose',
    'storages',
    'social.apps.django_app.default',
    'raven.contrib.django.raven_compat',
    'django_ace',
    'django_object_actions',
    'djcelery',
    'loginas',

    # OAuth
    'provider',
    'provider.oauth2',
    'corsheaders',

    # =================================
    # Project apps
    # =================================
    'beta_signup',
    'sa_api_v2',
    'sa_api_v2.apikey',
    'sa_api_v2.cors',
    'remote_client_user',
)

if USE_GEODB:
    INSTALLED_APPS += (
        # GeoDjango comes last so that we can override its admin templates.
        'django.contrib.gis',
    )


###############################################################################
#
# Background task processing
#

CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend'
CELERY_ACCEPT_CONTENT = ['json', 'msgpack', 'yaml', 'pickle']


###############################################################################
#
# Authentication
#

AUTHENTICATION_BACKENDS = (
    # See http://django-social-auth.readthedocs.org/en/latest/configuration.html
    # for list of available backends.
    'social.backends.twitter.TwitterOAuth',
    'social.backends.facebook.FacebookOAuth2',
    'sa_api_v2.auth_backends.CachedModelBackend',
)

AUTH_USER_MODEL = 'sa_api_v2.User'
SOCIAL_AUTH_USER_MODEL = 'sa_api_v2.User'
SOCIAL_AUTH_PROTECTED_USER_FIELDS = ['email',]

SOCIAL_AUTH_FACEBOOK_EXTRA_DATA = ['name', 'picture', 'about']
SOCIAL_AUTH_TWITTER_EXTRA_DATA = ['name', 'description', 'profile_image_url']

# Explicitly request the following extra things from facebook
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {'fields': 'id,name,picture.width(96).height(96),first_name,last_name,about'}

SOCIAL_AUTH_LOGIN_ERROR_URL = 'remote-social-login-error'


################################################################################
#
# Testing and administration
#

# Tests (nose)
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
SOUTH_TESTS_MIGRATE = True
SOUTH_MIGRATION_MODULES = {
    'oauth2': 'ignore',
    'djcelery': 'ignore',
}

# Debug toolbar
def custom_show_toolbar(request):
    return SHOW_DEBUG_TOOLBAR

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': 'project.settings.custom_show_toolbar',
    'INTERCEPT_REDIRECTS': False
}

INTERNAL_IPS = ('127.0.0.1',)
DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.cache.CachePanel',  # Disabled by default
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
)
# (See the very end of the file for more debug toolbar settings)


################################################################################
#
# Logging Configuration
#

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(name)s: %(message)s %(process)d %(thread)d'
        },
        'moderate': {
            'format': '%(levelname)s %(asctime)s %(name)s: %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'moderate'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'sa_api_v2': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },

        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },

        'utils.request_timer': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },

        'storages': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },

        'redis_cache': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

##############################################################################
# Environment loading

if 'DATABASE_URL' in environ:
    import dj_database_url
    # NOTE: Be sure that your DATABASE_URL has the 'postgis://' scheme.
    DATABASES = {'default': dj_database_url.config()}

    if USE_GEODB:
        DATABASES['default']['ENGINE'] = 'django.contrib.gis.db.backends.postgis'

if 'DEBUG' in environ:
    DEBUG = (environ['DEBUG'].lower() == 'true')
    TEMPLATE_DEBUG = DEBUG
    SHOW_DEBUG_TOOLBAR = DEBUG

# Look for the following redis environment variables, in order
for REDIS_URL_ENVVAR in ('REDIS_URL', 'OPENREDIS_URL'):
    if REDIS_URL_ENVVAR in environ: break
else:
    REDIS_URL_ENVVAR = None

if REDIS_URL_ENVVAR:
    import django_cache_url
    CACHES = {'default': django_cache_url.config(env=REDIS_URL_ENVVAR)}

    # Django sessions
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"

    # Celery broker
    BROKER_URL = environ[REDIS_URL_ENVVAR].strip('/') + '/1'

if all([key in environ for key in ('SHAREABOUTS_AWS_KEY',
                                   'SHAREABOUTS_AWS_SECRET',
                                   'SHAREABOUTS_AWS_BUCKET')]):
    AWS_ACCESS_KEY_ID = environ['SHAREABOUTS_AWS_KEY']
    AWS_SECRET_ACCESS_KEY = environ['SHAREABOUTS_AWS_SECRET']
    AWS_STORAGE_BUCKET_NAME = environ['SHAREABOUTS_AWS_BUCKET']
    AWS_QUERYSTRING_AUTH = False
    AWS_PRELOAD_METADATA = True

    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    ATTACHMENT_STORAGE = DEFAULT_FILE_STORAGE

if 'SHAREABOUTS_TWITTER_KEY' in environ \
    and 'SHAREABOUTS_TWITTER_SECRET' in environ:
    SOCIAL_AUTH_TWITTER_KEY = environ['SHAREABOUTS_TWITTER_KEY']
    SOCIAL_AUTH_TWITTER_SECRET = environ['SHAREABOUTS_TWITTER_SECRET']

if 'SHAREABOUTS_FACEBOOK_KEY' in environ \
    and 'SHAREABOUTS_FACEBOOK_SECRET' in environ:
    SOCIAL_AUTH_FACEBOOK_KEY = environ['SHAREABOUTS_FACEBOOK_KEY']
    SOCIAL_AUTH_FACEBOOK_SECRET = environ['SHAREABOUTS_FACEBOOK_SECRET']


if 'SHAREABOUTS_ADMIN_EMAIL' in environ:
    ADMINS = (
        ('Shareabouts API Admin', environ.get('SHAREABOUTS_ADMIN_EMAIL')),
    )

if 'CONSOLE_LOG_LEVEL' in environ:
    LOGGING['handlers']['console']['level'] = environ.get('CONSOLE_LOG_LEVEL')

##############################################################################
# Local GEOS/GDAL installations (for Heroku)

import os.path

if os.path.exists('/app/.geodjango/geos/lib/libgeos_c.so'):
    GEOS_LIBRARY_PATH = '/app/.geodjango/geos/lib/libgeos_c.so'

if os.path.exists('/app/.geodjango/gdal/lib/libgdal.so'):
    GDAL_LIBRARY_PATH = '/app/.geodjango/gdal/lib/libgdal.so'

##############################################################################
# Local settings overrides
# ------------------------
# Override settings values by importing the local_settings.py module.

try:
    from .local_settings import *
except ImportError:
    pass


##############################################################################
# More background processing
#

try:
    BROKER_URL
except NameError:
    BROKER_URL = 'django://'

if BROKER_URL == 'django://':
    INSTALLED_APPS += ('kombu.transport.django', )


##############################################################################
# Debug Toolbar
# ------------------------
# Do this after all the settings files have been processed, in case the
# SHOW_DEBUG_TOOLBAR setting is set.

# if SHOW_DEBUG_TOOLBAR:
#     INSTALLED_APPS += ('debug_toolbar',)
#     MIDDLEWARE_CLASSES = (
#         MIDDLEWARE_CLASSES[:2] +
#         ('debug_toolbar.middleware.DebugToolbarMiddleware',) +
#         MIDDLEWARE_CLASSES[2:]
#     )
