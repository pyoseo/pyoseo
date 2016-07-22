"""Django settings for pyoseo project.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/

"""

import os

from django.core.exceptions import ImproperlyConfigured
from celery.schedules import crontab
import pathlib2


def get_environment_variable(var_name, mandatory=False):
    value = os.getenv(var_name)
    if value is None and mandatory:
        error_msg = "Set the {0} environment variable".format(var_name)
        raise ImproperlyConfigured(error_msg)
    return value


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = str(pathlib2.Path(__file__).parents[2])


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_environment_variable("SECRET_KEY", mandatory=True)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'grappelli',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'mailqueue',  # required by oseoserver
    'oseoserver',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")

#SITE_ID = 1

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(levelname)s %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": "DEBUG"
        }
    },
    "loggers": {
        "oseoserver": {
            "handlers": ["console"],
            "level": "DEBUG"
        }
    }
}

for mail_setting in ("EMAIL_HOST",
                     "EMAIL_PORT",
                     "EMAIL_HOST_USER",
                     "EMAIL_HOST_PASSWORD"):
    value = get_environment_variable(mail_setting)
    if value is not None:
        globals()[mail_setting] = value


CELERY_SEND_TASK_ERROR_EMAILS = True
SERVER_EMAIL = globals().get("EMAIL_HOST_USER", "")
CELERY_IGNORE_RESULT = False
CELERY_RESULT_BACKEND = "redis://"
CELERY_TASK_RESULT_EXPIRES = 18000  # 5 hours
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_REDIRECT_STDOUTS = True
CELERY_HIJACK_ROOT_LOGGER = False
CELERY_DISABLE_RATE_LIMITS = True

CELERYBEAT_SCHEDULE = {
    "delete_expired_order_items": {
        "task": "oseoserver.tasks.delete_expired_order_items",
        "schedule": crontab(hour=10, minute=30)  # execute daily at 10h30
    },
    "delete_failed_orders": {
        "task": "oseoserver.tasks.delete_failed_orders",
        "schedule": crontab(hour=11, minute=30)  # execute daily at 11h30
    },
}

MAILQUEUE_CELERY = True

SENDFILE_BACKEND = "sendfile.backends.simple"

