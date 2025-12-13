from pathlib import Path
from datetime import timedelta
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "your-secret-key"
DEBUG = False   # ✅ MUST be False on Render

ALLOWED_HOSTS = [
    "food-crm-backend.onrender.com",
    "localhost",
    "127.0.0.1",
]

# ----------------------------
# INSTALLED APPS
# ----------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "corsheaders",
    "rest_framework_simplejwt",

    "foodapp",
]

AUTH_USER_MODEL = "foodapp.User"

# ----------------------------
# MIDDLEWARE
# ----------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # MUST BE FIRST
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "foodproject.urls"

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

WSGI_APPLICATION = "foodproject.wsgi.application"

# ----------------------------
# DATABASE
# ----------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

# ----------------------------
# GLOBAL
# ----------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ----------------------------
# EMAIL (GMAIL SMTP)
# ----------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "pateldhruv8404@gmail.com"
EMAIL_HOST_PASSWORD = "chqmyfrojxnpwtid"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ----------------------------
# FRONTEND BASE URL (IMPORTANT)
# ----------------------------
FRONTEND_BASE_URL = (
    "https://rood-crm-frontend-hixi9de0e-pateldhruv8404-4868s-projects.vercel.app"
)

# ----------------------------
# CORS SETTINGS (FINAL)
# ----------------------------
CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOWED_ORIGINS = [
    FRONTEND_BASE_URL,
]

# allow all Vercel preview URLs
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    "authorization",
    "content-type",
    "accept",
    "origin",
    "user-agent",
    "x-csrftoken",
]

CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]

CORS_EXPOSE_HEADERS = ["Content-Type", "Authorization"]

# ----------------------------
# CSRF
# ----------------------------
CSRF_TRUSTED_ORIGINS = [
    "https://food-crm-backend.onrender.com",
    FRONTEND_BASE_URL,
]

# ----------------------------
# REST + JWT
# ----------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

# ----------------------------
# RAZORPAY
# ----------------------------
RAZORPAY_KEY_ID = "rzp_test_hf54kCj6NjigUj"
RAZORPAY_SECRET = "GmCuH0pPD5BS582jPdhzDycp"
