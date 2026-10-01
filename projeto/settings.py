"""
Django settings for projeto project.
"""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default):
    value = os.getenv(name)
    if not value:
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


DEBUG = env_bool("DJANGO_DEBUG", True)

_DEV_SECRET_KEY = "django-insecure-local-development-only"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", _DEV_SECRET_KEY)

if not DEBUG and SECRET_KEY == _DEV_SECRET_KEY:
    raise RuntimeError(
        "DJANGO_SECRET_KEY precisa ser definida no ambiente quando DJANGO_DEBUG=False."
    )

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    [
        "aguiacafe.com.br",
        "www.aguiacafe.com.br",
        "127.0.0.1",
        "localhost",
    ],
)

CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    [
        "https://aguiacafe.com.br",
        "https://www.aguiacafe.com.br",
    ],
)


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "clientes",
    "produtos",
    "vendas",
    "fiado",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "projeto.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "projeto.wsgi.application"


DB_ENGINE = os.getenv("DJANGO_DB_ENGINE", "sqlite").strip().lower()

if DB_ENGINE in {"postgres", "postgresql"}:
    required_db_vars = ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST"]
    missing_db_vars = [name for name in required_db_vars if not os.getenv(name)]

    if missing_db_vars:
        raise RuntimeError(
            "Configuração PostgreSQL incompleta. Variáveis ausentes: "
            + ", ".join(missing_db_vars)
        )

    database_options = {}
    db_sslmode = os.getenv("DB_SSLMODE", "").strip()
    if db_sslmode:
        database_options["sslmode"] = db_sslmode

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["DB_NAME"],
            "USER": os.environ["DB_USER"],
            "PASSWORD": os.environ["DB_PASSWORD"],
            "HOST": os.environ["DB_HOST"],
            "PORT": os.getenv("DB_PORT", "5432"),
            # CGI cria um novo processo por requisição; conexão persistente
            # não traz benefício neste tipo de deploy.
            "CONN_MAX_AGE": 0,
            "OPTIONS": database_options,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


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


LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True


STATIC_URL = "/static/"
STATIC_ROOT = Path(os.getenv("DJANGO_STATIC_ROOT", BASE_DIR / "staticfiles"))


SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

# Ative somente depois que o HTTPS estiver funcionando no domínio.
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", False)

# Pode ser aumentado depois que HTTPS estiver estável.
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_HSTS_PRELOAD = False


LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"
