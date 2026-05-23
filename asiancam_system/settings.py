"""
Django settings for asiancam_system project.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# =========================
# BASIC SETTINGS
# =========================

SECRET_KEY = "django-insecure-rid(&r0%0fl4o%5c4cqmt1p9+7s8)zu!!c2sp4(whb7)ux&7n%"

DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "5.223.90.183",
]


# =========================
# APPLICATIONS
# =========================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # AsianCam apps
    "dashboard",
    "core.apps.CoreConfig",
    "clients",
    "workspaces",
    "reports",

    # Accounting apps
    "accounting",
    "vendors",
    "stock",
    "customers",
    "accounting_ops",
]


# =========================
# MIDDLEWARE
# =========================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# =========================
# URL / WSGI
# =========================

ROOT_URLCONF = "asiancam_system.urls"

WSGI_APPLICATION = "asiancam_system.wsgi.application"


# =========================
# TEMPLATES
# =========================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# =========================
# DATABASE
# =========================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# =========================
# PASSWORD VALIDATION
# =========================

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


# =========================
# LANGUAGE / TIMEZONE
# =========================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Phnom_Penh"

USE_I18N = True

USE_TZ = True


# =========================
# STATIC / MEDIA
# =========================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# =========================
# DEFAULT PRIMARY KEY
# =========================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# =========================
# LOGIN SETTINGS
# =========================

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard_home"
LOGOUT_REDIRECT_URL = "login"