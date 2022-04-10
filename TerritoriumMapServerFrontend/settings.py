#  Copyright 2019-2022 Simon Zigelli
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import asyncio
import json
import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from environ import environ

env = environ.Env(
    DEBUG=(bool, False)
)

PROJECT_PACKAGE = Path(__file__).resolve().parent
BASE_DIR = Path(PROJECT_PACKAGE).resolve().parent
env.read_env(env_file=os.path.join(BASE_DIR, ".env"))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")
SHOW_DEBUG_TOOLBAR = DEBUG

VERSION = "0.1.0-alpha01"

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["https://127.0.0.1", "https://localhost"])

RABBITMQ_URL = env.str("RABBITMQ_URL", default="amqp://tms:tms@localhost:5672/%2F")

EXCHANGE_DIR = env.str("EXCHANGE_DIR", default="/input/")

MAX_POLYGONS = env.str("MAX_POLYGONS", default=9)

# Application definition

INSTALLED_APPS = [
    'receiver',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.forms',
    'fileserver.apps.FileserverConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
)

ROOT_URLCONF = 'TerritoriumMapServerFrontend.urls'
LOGIN_REDIRECT_URL = '/files/list/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
LOGIN_URL = '/accounts/login/'

DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="webmaster@localhost")
EMAIL_CONFIG = env.email_url(default="smtp://user:password@localhost:25")
EMAIL_SEND_URL = env.str("EMAIL_SEND_URL", default="http://localhost:8000")

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

WSGI_APPLICATION = 'TerritoriumMapServerFrontend.wsgi.application'

DATABASES = {
    "default": env.db_url(default="sqlite:///db.sqlite3")
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGES = [(x.split(":")[0], _(x.split(":")[1])) for x in env.list("LANGUAGES", default=["de:German", "en:English"])]

if not [item for item in LANGUAGES if item[0] == env.str("DEFAULT_LANGUAGE", default="de")]:
    raise ImproperlyConfigured("Language list does not contain the default language.")

LANGUAGE_CODE = env.str("DEFAULT_LANGUAGE", default="de")

LOCALE_PATHS = (
    str(PROJECT_PACKAGE.joinpath("locale")),
)

TIME_ZONE = env.str("TIME_ZONE", default="Europe/Berlin")

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = "/static/assets/"
STATIC_ROOT = os.path.join(BASE_DIR, "static/assets")
STATICFILES_DIRS = [("TerritoriumMapServerFrontend", str(PROJECT_PACKAGE.joinpath("static")))]

MEDIA_URL = "/files/"
MEDIA_ROOT = os.path.join(BASE_DIR, "files/")

if DEBUG:
    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = env.str("SECRET_KEY", "django-insecure-qhmmb46a$-j_#%yt0@1enx=mxpercrdbu!sc4^x=a1n_+a!^y5")
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

    import mimetypes

    mimetypes.add_type("application/javascript", ".js", True)
    try:
        import debug_toolbar
    except ImportError:
        pass
    else:
        INSTALLED_APPS.append("debug_toolbar")
        INTERNAL_IPS = ["127.0.0.1"]
        MIDDLEWARE.insert(
            MIDDLEWARE.index("django.middleware.common.CommonMiddleware") + 1,
            "debug_toolbar.middleware.DebugToolbarMiddleware"
        )
else:
    SECRET_KEY = env.str("SECRET_KEY")

    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
    SESSION_COOKIE_AGE = 43200
