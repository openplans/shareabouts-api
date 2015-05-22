from __future__ import print_function
import os
import re

DEBUG = True
SHOW_DEBUG_TOOLBAR = False

def read_env():
    """Pulled from Honcho code with minor updates, reads local default
    environment variables from a .env file located in the project root
    directory.

    """
    try:
        file_path = os.path.join(os.path.dirname(__file__), '..',  '.env')
        # print "filepath:" + str(file_path)
        with open(file_path) as f:
            content = f.read()
    except IOError:
        content = ''

    for line in content.splitlines():
        m1 = re.match(r'\A([A-Za-z_0-9]+)=(.*)\Z', line)
        if m1:
            key, val = m1.group(1), m1.group(2)
            m2 = re.match(r"\A'(.*)'\Z", val)
            if m2:
                val = m2.group(1)
            m3 = re.match(r'\A"(.*)"\Z', val)
            if m3:
                val = re.sub(r'\\(.)', r'\1', m3.group(1))
            os.environ.setdefault(key, val)
read_env()

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'shareabouts_v2',
        'USER': os.environ['USERNAME'],
        'PASSWORD': os.environ['PASS'],
        'HOST': 'localhost',
        # For dockerization:
        # 'HOST': 'postgis',
        'PORT': '5432',
    }
}

REST_FRAMEWORK = {
    'PAGINATE_BY': 500,
    'PAGINATE_BY_PARAM': 'page_size'
}

BROKER_URL = 'django://'

# Set the attachment storage class to the file storage class that should
# manage storing and retriving of place and submission attachments.
#
# ATTACHMENT_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Duwamish account settings:
SOCIAL_AUTH_TWITTER_KEY = os.environ['SOCIAL_AUTH_TWITTER_KEY']
SOCIAL_AUTH_TWITTER_SECRET = os.environ['SOCIAL_AUTH_TWITTER_SECRET']

SOCIAL_AUTH_FACEBOOK_KEY = os.environ['SOCIAL_AUTH_FACEBOOK_KEY']
SOCIAL_AUTH_FACEBOOK_SECRET = os.environ['SOCIAL_AUTH_FACEBOOK_SECRET']

# Django will use django.core.files.storage.FileSystemStorage by default.
# Uncomment the following lines if you want to use S3 storage instead.
#
ATTACHMENT_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
# AWS_ACCESS_KEY_ID = ''
# AWS_SECRET_ACCESS_KEY = ''
# AWS_STORAGE_BUCKET_NAME = 'shareabouts_attachments'
# AWS_QUERYSTRING_AUTH = False

# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
# ATTACHMENT_STORAGE = DEFAULT_FILE_STORAGE
# STATICFILES_STORAGE = DEFAULT_FILE_STORAGE

AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
# STATIC_URL = 'https://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME
AWS_QUERYSTRING_AUTH = False

LAUNCHROCK_KEY = os.environ['LAUNCHROCK_KEY']

# Some default settings that are handy for debugging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(name)s %(process)d %(thread)d %(message)s'
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
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'moderate'
        },
        'debug_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'moderate',

            'filename': 'debug.log',
            'backupCount': 3,
            'when': 'h',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['debug_file'],
            'level': 'DEBUG',
            'propagate': True,
            },
        # 'raven': {
        #     'level': 'ERROR',
        #     'handlers': ['console'],
        #     'propagate': True,
        #     },
        'utils.request_timer': {
            'handlers': ['debug_file'],
            'level': 'DEBUG',
            'propagate': True,
            },

        'storages': {
            'handlers': ['debug_file'],
            'level': 'DEBUG',
            'propagate': True,
            },

        'redis_cache': {
            'handlers': ['debug_file'],
            'level': 'DEBUG',
            'propagate': True,
            },

        'sa_api': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
            },
        }
}
