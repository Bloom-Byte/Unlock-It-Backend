import os
from pathlib import Path
import re

from environs import Env


env = Env()
env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
# sys.path.insert(0, os.path.join(BASE_DIR, "apps"))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.str("ALLOWED_HOSTS").split(",")


SESSION_COOKIE_SECURE = False

CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = env.bool("CORS_ORIGIN_ALLOW_ALL", default=True)
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=True)
CSRF_COOKIE_SECURE = False

CORS_URLS_REGEX = r"^/api/.*$"


# the values will have https://
CORS_ALLOWED_ORIGINS = env.str("CORS_ALLOWED_ORIGINS").split(",")

# the values will have https://
CSRF_TRUSTED_ORIGINS = env.str("CSRF_TRUSTED_ORIGINS").split(",")


# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "drf_yasg",
]


SELF_APPS = [
    "app",
]


INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + SELF_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "app.middlewares.Log500ErrorsMiddleware",
    "djangorestframework_camel_case.middleware.CamelCaseMiddleWare",
]

ROOT_URLCONF = "UnlockIt.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "UnlockIt.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

if "LIVE" in os.environ:
    DATABASES = {
        "default": env.dj_db_url(
            "DATABASE_URL",
        ),
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/


STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATICFILES_DIRS = (os.path.join(BASE_DIR, "staticfiles"),)

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"  # new


# MEDIA Folder settings
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# overriding user model
AUTH_USER_MODEL = "app.CustomUser"


# overriding authentication backend
AUTHENTICATION_BACKENDS = ["app.custom_authentication.CustomAuthenticationBackend"]


# setting restframework authentication class
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "app.api_authentication.MyAPIAuthentication",
    ],
    "DEFAULT_RENDERER_CLASSES": (
        "djangorestframework_camel_case.render.CamelCaseJSONRenderer",
        "djangorestframework_camel_case.render.CamelCaseBrowsableAPIRenderer",
        # Any other renders
    ),
    "DEFAULT_PARSER_CLASSES": (
        # If you use MultiPartFormParser or FormParser, we also have a camel case version
        "djangorestframework_camel_case.parser.CamelCaseFormParser",
        "djangorestframework_camel_case.parser.CamelCaseMultiPartParser",
        "djangorestframework_camel_case.parser.CamelCaseJSONParser",
        # Any other parsers
    ),
}


# settings for swagger documentation
SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {"Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"}},
    "PERSIST_AUTH": True,
    "USE_SESSION_AUTH": False,
    "DEFAULT_MODEL_RENDERING": "example",
}


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] -> %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "django.server": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "server_error": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}


IGNORABLE_404_URLS = [
    re.compile(r"^/apple-touch-icon.*\.png$"),
    re.compile(r"^/favicon\.ico$"),
    re.compile(r"^/undefined$"),
    re.compile(r"^/robots\.txt$"),
    re.compile(r"\.(php|cgi)$"),
]

GENERATE_CODE = env.bool("GENERATE_CODE", default=False)
DEFAULT_OTP = "123456"
OTP_EXPIRATION_MINUTES = 5
OTP_GENERATE_TIME_LAPSE_MINUTES = 1
MAX_LOGIN_ATTEMPTS = 4


RUN_BACKGROUND_TASK = False

# if "REDIS_URL" in os.environ:
#     RUN_BACKGROUND_TASK = True

#     # REDIS localhost settings
#     REDIS_HOST = "localhost"
#     REDIS_PORT = "6379"

#     # Celery Configuration Options
#     CELERY_BROKER_TRANSPORT_OPTIONS = {"visibility_timeout": 3600}

#     CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://" + REDIS_HOST + ":" + REDIS_PORT)
#     CELERY_ACCEPT_CONTENT = ["application/json"]
#     CELERY_RESULT_SERIALIZER = "json"
#     CELERY_TASK_SERIALIZER = "json"
#     CELERY_TIMEZONE = "Africa/Lagos"

#     # stores your tasks status in django database
#     CELERY_RESULT_BACKEND = "django-db"

#     # Celery beat Setting
#     CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"


# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.redis.RedisCache",
#         "LOCATION": os.environ.get("REDIS_URL", "redis://" + REDIS_HOST + ":" + REDIS_PORT),
#         "TIMEOUT": 600,
#     }
# }


DATA_UPLOAD_MAX_MEMORY_SIZE = None

FILE_UPLOAD_MAX_SIZE_MB = 100


SHOW_DOCS = env.bool("SHOW_DOCS")


GOOGLE_OAUTH2_CLIENT_ID = env.str("GOOGLE_OAUTH2_CLIENT_ID")
GOOGLE_OAUTH2_CLIENT_SECRET = env.str("GOOGLE_OAUTH2_CLIENT_SECRET")

GOOGLE_ID_TOKEN_INFO_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo"
GOOGLE_ACCESS_TOKEN_OBTAIN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


FACEBOOK_OAUTH_CLIENT_ID = env.str("FACEBOOK_OAUTH_CLIENT_ID")
FACEBOOK_OAUTH_CLIENT_SECRET = env.str("FACEBOOK_OAUTH_CLIENT_SECRET")
FACEBOOK_ACCESS_TOKEN_OBTAIN_URL = "https://graph.facebook.com/v19.0/oauth/access_token"
FACEBOOK_PROFILE_ENDPOINT_URL = "https://graph.facebook.com/me"


DEFAULT_FILE_STORAGE = "storages.backends.s3.S3Storage"

AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME")
AWS_QUERYSTRING_AUTH = env.str("AWS_QUERYSTRING_AUTH")
AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY")
