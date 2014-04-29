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

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# OSEOSERVER OPTIONS
OSEOSERVER_AUTHENTICATION_CLASS = None # redefined in the settings_local.py module
OSEOSERVER_MASSIVE_ORDER_REFERENCE = 'Massive order'
OSEOSERVER_ONLINE_DATA_ACCESS_HTTP_PROTOCOL_ROOT_DIR = '/var/www'
OSEOSERVER_ONLINE_DATA_ACCESS_FTP_PROTOCOL_ROOT_DIR = '/var/www'

# GIOSYSTEM SPECIFIC
GIOSYSTEM_SETTINGS_URL = '' # redefined in the settings_local.py module

# CELERY OPTIONS
CELERY_RESULT_BACKEND = 'amqp'
CELERY_TASK_RESULT_EXPIRES = 18000 # 5 hours
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_REDIRECT_STDOUTS = True
#CELERY_REDIRECT_STDOUTS_LEVEL = 'DEBUG'
CELERYD_HIJACK_ROOT_LOGGER = False
CELERY_IGNORE_RESULT = False
CELERY_DISABLE_RATE_LIMITS = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'adc!i+t)9(r^(++at!t^+ke_9#vnrnsrp_z1(8!dthyt38ae5r'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

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
