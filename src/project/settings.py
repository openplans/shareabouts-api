from os import environ

DEBUG = True
SHOW_DEBUG_TOOLBAR = DEBUG
DEBUG_TOOLBAR_PATCH_SETTINGS = False

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

USE_GEODB = (environ.get('USE_GEODB', 'True').lower() == 'true')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                       # Or path to database file if using sqlite3.
        'USER': '',                       # Not used with sqlite3.
        'PASSWORD': '',                   # Not used with sqlite3.
        'HOST': '',                       # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                       # Set to empty string for default. Not used with sqlite3.
    }
}
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

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

TIME_ZONE = 'UTC'
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

STATIC_ROOT = 'staticfiles'
STATIC_URL = '/static/'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
STATICFILES_DIRS = ()

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
            ],
            'debug': DEBUG,
        },
    },
]

ATTACHMENT_STORAGE = 'django.core.files.storage.FileSystemStorage'

###############################################################################
#
# Django Rest Framework
#
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'PAGINATE_BY_PARAM': 'page_size'
}

###############################################################################
#
# Request/Response processing
#

WSGI_APPLICATION = 'project.wsgi.application'
ROOT_URLCONF = 'project.urls'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django_samesite_none.middleware.SameSiteNoneMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'dynamic_social_auth.middleware.DynamicSocialAuthMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    'sa_api_v2.middleware.RequestTimeLogger',
    'sa_api_v2.middleware.UniversalP3PHeader',
]

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
    'storages',
    'django_ace',
    'django_object_actions',
    'django_celery_results',
    'loginas',

    # The old-style social.apps.django_app below is needed just for migrations.
    # Uncomment the first of the following two lines and run manage.py migrate. After
    # that, comment out the old-style social app again. Note that exactly one of the
    # following lines should be uncommented at a time.
    #
    # 'social.apps.django_app.default',  # <-- Just for migrations; replaced by social_django
    'social_django',

    # CORS
    'corsheaders',

    # =================================
    # Project apps
    # =================================
    'dynamic_social_auth',
    'beta_signup',
    'sa_api_v2',
    'sa_api_v2.apikey',
    'sa_api_v2.cors',
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

CELERY_RESULT_BACKEND = 'django_celery_results.backends:DatabaseBackend'
CELERY_CACHE_BACKEND = 'default'
CELERY_ACCEPT_CONTENT = ['json', 'msgpack', 'yaml', 'pickle']


###############################################################################
#
# Authentication
#

AUTHENTICATION_BACKENDS = (
    # See https://python-social-auth.readthedocs.io/en/latest/backends/index.html#supported-backends
    # for list of available backends.
    'dynamic_social_auth.backends.DynamicProviderModelAuth',
    'social_core.backends.twitter.TwitterOAuth',
    'social_core.backends.facebook.FacebookOAuth2',
    'sa_api_v2.auth_backends.CachedModelBackend',
)

# In addition to the backends listed above, we use a dynamic strategy to take
# into account providers defined in database models.
SOCIAL_AUTH_STRATEGY = 'dynamic_social_auth.strategy.DjangoModelStrategy'

AUTH_USER_MODEL = 'sa_api_v2.User'

# TODO: Enable after Django 1.11 update # SOCIAL_AUTH_POSTGRES_JSONFIELD = True
SOCIAL_AUTH_URL_NAMESPACE = 'social'

SOCIAL_AUTH_USER_MODEL = 'sa_api_v2.User'
SOCIAL_AUTH_PROTECTED_USER_FIELDS = ['email',]

SOCIAL_AUTH_FACEBOOK_EXTRA_DATA = ['name', 'picture', 'about']
SOCIAL_AUTH_TWITTER_EXTRA_DATA = ['name', 'description', 'profile_image_url']

# Explicitly request the following extra things from facebook
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {'fields': 'id,name,picture.width(96).height(96),first_name,last_name,about'}

# SOCIAL_AUTH_LOGIN_ERROR_URL = 'remote-social-login-error'

LOGIN_REDIRECT_URL = '/api/v2/users/current'


################################################################################
#
# Testing and administration
#

# Debug toolbar
def custom_show_toolbar(request):
    return SHOW_DEBUG_TOOLBAR


DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': 'project.settings.custom_show_toolbar',
    'DISABLE_PANELS': {}
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

        # 'django.db.backends': {
        #     'handlers': ['console'],
        #     'level': 'DEBUG',
        #     'propagate': True,
        # },

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

if 'SENTRY_DSN' in environ:
    import sentry_sdk
    sentry_sdk.init(enable_tracing=True)

if 'DATABASE_URL' in environ:
    import dj_database_url
    # NOTE: Be sure that your DATABASE_URL has the 'postgis://' scheme.
    DATABASES = {'default': dj_database_url.config()}

    if USE_GEODB:
        DATABASES['default']['ENGINE'] = 'django.contrib.gis.db.backends.postgis'

elif all([key in environ for key in ('DB_PASSWORD', 'DATABASE_HOST', 'DATABASE_NAME', 'DATABASE_USER')]):
    # Construct DATABASE_URL from components (Cloud Run Secrets approach)
    db_user = environ['DATABASE_USER']
    db_password = environ['DB_PASSWORD']
    db_host = environ['DATABASE_HOST']
    db_name = environ['DATABASE_NAME']

    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis' if USE_GEODB else 'django.db.backends.postgresql',
            'NAME': db_name,
            'USER': db_user,
            'PASSWORD': db_password,
            'HOST': db_host,
            'PORT': '5432',
        }
    }

if 'DEBUG' in environ:
    DEBUG = (environ['DEBUG'].lower() == 'true')
    TEMPLATES[0]['OPTIONS']['debug'] = DEBUG
    SHOW_DEBUG_TOOLBAR = DEBUG

# Look for the following redis environment variables, in order
for REDIS_URL_ENVVAR in ('REDIS_URL', 'OPENREDIS_URL'):
    if REDIS_URL_ENVVAR in environ:
        break
else:
    REDIS_URL_ENVVAR = None

if REDIS_URL_ENVVAR:
    import django_cache_url
    CACHE_CONFIG = django_cache_url.config(env=REDIS_URL_ENVVAR)

    # Override to use the django-redis backend
    CACHE_CONFIG['BACKEND'] = 'django_redis.cache.RedisCache'
    CACHE_CONFIG.setdefault('OPTIONS', {}).update({
        "CLIENT_CLASS": "django_redis.client.DefaultClient",
    })

    # Use TLS if the REDIS_USE_TLS environment variable is set to true
    if environ.get('REDIS_USE_TLS', 'false').lower() == 'true':
        CACHE_CONFIG.setdefault('OPTIONS', {}).update({
            "CONNECTION_POOL_KWARGS": {
                "ssl_cert_reqs": None
            },
        })

    CACHES = {'default': CACHE_CONFIG}

    # Django sessions
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"

    # Celery broker
    CELERY_BROKER_URL = environ[REDIS_URL_ENVVAR].strip('/') + '/1'

# Storage Configuration
# ---------------------
# We support S3, GCS, and local filesystem.
# Precedence: GCS > S3 > Local

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
ATTACHMENT_STORAGE = DEFAULT_FILE_STORAGE

if 'GS_BUCKET_NAME' in environ:
    # Google Cloud Storage
    GS_BUCKET_NAME = environ['GS_BUCKET_NAME']
    GS_PROJECT_ID = environ.get('GS_PROJECT_ID')

    DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
    STATICFILES_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"

    GS_DEFAULT_ACL = "publicRead"

    # Static files
    STATIC_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/static/"

    # Media files
    MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/media/"

    # Attachments
    ATTACHMENT_STORAGE = DEFAULT_FILE_STORAGE

elif all([key in environ for key in ('SHAREABOUTS_AWS_KEY',
                                     'SHAREABOUTS_AWS_SECRET',
                                     'SHAREABOUTS_AWS_BUCKET')]):
    # AWS S3
    AWS_ACCESS_KEY_ID = environ['SHAREABOUTS_AWS_KEY']
    AWS_SECRET_ACCESS_KEY = environ['SHAREABOUTS_AWS_SECRET']
    AWS_STORAGE_BUCKET_NAME = environ['SHAREABOUTS_AWS_BUCKET']
    AWS_QUERYSTRING_AUTH = False
    AWS_PRELOAD_METADATA = True

    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    ATTACHMENT_STORAGE = DEFAULT_FILE_STORAGE


if 'SHAREABOUTS_TWITTER_KEY' in environ and 'SHAREABOUTS_TWITTER_SECRET' in environ:
    SOCIAL_AUTH_TWITTER_KEY = environ['SHAREABOUTS_TWITTER_KEY']
    SOCIAL_AUTH_TWITTER_SECRET = environ['SHAREABOUTS_TWITTER_SECRET']

if 'SHAREABOUTS_FACEBOOK_KEY' in environ and 'SHAREABOUTS_FACEBOOK_SECRET' in environ:
    SOCIAL_AUTH_FACEBOOK_KEY = environ['SHAREABOUTS_FACEBOOK_KEY']
    SOCIAL_AUTH_FACEBOOK_SECRET = environ['SHAREABOUTS_FACEBOOK_SECRET']

# Load in any other social auth keys and secrets from the environment
for key in environ:
    if key.startswith('SOCIAL_AUTH_') and (key.endswith('_KEY') or key.endswith('_SECRET')):
        globals()[key] = environ[key]


if 'SHAREABOUTS_ADMIN_EMAIL' in environ:
    ADMINS = (
        ('Shareabouts API Admin', environ.get('SHAREABOUTS_ADMIN_EMAIL')),
    )

if 'CONSOLE_LOG_LEVEL' in environ:
    LOGGING['handlers']['console']['level'] = environ.get('CONSOLE_LOG_LEVEL')


##############################################################################
# Local settings overrides
# ------------------------
# Override settings values by importing the local_settings.py module.

try:
    from .local_settings import *  # noqa  # type: ignore
except ImportError:
    pass


##############################################################################
# More background processing
#

try:
    CELERY_BROKER_URL
except NameError:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(  # pylint: disable=raise-missing-from
        'Expected CELERY_BROKER_URL or REDIS_URL\n'
        '\n'
        'Since Celery 4, Django backend is no longer supported. Specify a '
        'broker URL in your environment with CELERY_BROKER_URL, or by setting '
        'the REDIS_URL environment variable to use Redis as the broker.'
    )


##############################################################################
# Debug Toolbar
# ------------------------
# Do this after all the settings files have been processed, in case the
# SHOW_DEBUG_TOOLBAR setting is set.

if SHOW_DEBUG_TOOLBAR:
    INSTALLED_APPS += ('debug_toolbar',)
    # Add the debug toolbar middleware after the GZip middleware, but before
    # everything else.
    DEBUG_TOOLBAR_MIDDLWARE_INDEX = MIDDLEWARE.index('django.middleware.gzip.GZipMiddleware') + 1
    MIDDLEWARE = (
        MIDDLEWARE[:DEBUG_TOOLBAR_MIDDLWARE_INDEX] +
        ['debug_toolbar.middleware.DebugToolbarMiddleware'] +
        MIDDLEWARE[DEBUG_TOOLBAR_MIDDLWARE_INDEX:]
    )
