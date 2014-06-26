"""
Django settings for pyoseo project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

from celery.schedules import crontab

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# OSEOSERVER OPTIONS
OSEOSERVER_MASSIVE_ORDER_REFERENCE = 'Massive order'
OSEOSERVER_ORDER_DELETION_THRESHOLD = 5 #: in days
OSEOSERVER_ONLINE_DATA_ACCESS_HTTP_PROTOCOL_ROOT_DIR = '/home/ftpuser'
OSEOSERVER_ONLINE_DATA_ACCESS_FTP_PROTOCOL_ROOT_DIR = '/home/ftpuser'
OSEOSERVER_AUTHENTICATION_CLASS = None # redefined in settings_local
OSEOSERVER_PROCESSING_CLASS = None # redefined in settings_local

# GIOSYSTEM SPECIFIC
#GIOSYSTEM_SETTINGS_URL = '' # redefined in settings_local

# CELERY OPTIONS
CELERY_RESULT_BACKEND = 'redis://'
CELERY_TASK_RESULT_EXPIRES = 18000 #: 5 hours
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_REDIRECT_STDOUTS = True
CELERYD_HIJACK_ROOT_LOGGER = False
CELERY_IGNORE_RESULT = False
CELERY_DISABLE_RATE_LIMITS = True

#: pyoseo-beat schedule for executing periodic tasks
CELERYBEAT_SCHEDULE = {
        'monitor_ftp' : {
            'task': 'oseoserver.tasks.monitor_ftp_downloads',
            'schedule': crontab(hour=9, minute=30), # execute daily at 09:30
        },
        'clean_old_orders' : {
            'task': 'oseoserver.tasks.delete_old_orders',
            'schedule': crontab(hour=10, minute=30), # execute daily at 10:30
        },
}


def find_or_create_secret_key():
    '''
    Look for secret_key.py and return the SECRET_KEY entry in it if the file 
    exists. Otherwise, generate a new secret key, save it in secret_key.py, 
    and return the key.

    Adapted from Miles Steel's blog at
    http://blog.milessteele.com/posts/2013-07-07-hiding-djangos-secret-key.html
    '''

    secret_key_filepath = os.path.join(os.path.dirname(__file__), 'secret_key.py')
    if not os.path.isfile(secret_key_filepath):
        from django.utils.crypto import get_random_string
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&amp;*(-_=+)'
        new_key = get_random_string(50, chars)
        with file(secret_key_filepath, 'w') as fh:
            fh.write('# Django secret key\n')
            fh.write('# Do NOT check this into version control.\n\n')
            fh.write('SECRET_KEY = "{}"\n'.format(new_key))
    from secret_key import SECRET_KEY
    result = SECRET_KEY
    return result

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = find_or_create_secret_key()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False # redefined in settings_local

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'oseoserver',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'pyoseo.urls'

WSGI_APPLICATION = 'pyoseo.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'sitestatic')
STATIC_URL = '/static/'

# Logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'DEBUG',
        },
    },
    #'root': {
    #    'level': 'NOTSET',
    #    'handlers': ['console'],
    #},
    'loggers': {
        'pyoseo': {
            'handlers': ['console',],
            'level': 'DEBUG',
        },
    },
}

try:
    from settings_local import *
except ImportError:
    pass
