#!/bin/sh
set -eu

DOMAIN="${DOMAIN:-aguiacafe.com.br}"
APP_DIR="${APP_DIR:-$HOME/djangoprojects/Projeto-PDV}"
VENV_DIR="${VENV_DIR:-$HOME/virtualenvs/aguiacafe}"
WEBROOT="${WEBROOT:-$HOME/public_html/$DOMAIN}"
ENV_FILE="${ENV_FILE:-$HOME/.config/aguiacafe.env}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "== Águia Café / Hetzner Webhosting =="
echo "APP_DIR:  $APP_DIR"
echo "VENV_DIR: $VENV_DIR"
echo "WEBROOT:  $WEBROOT"

if [ ! -f "$APP_DIR/manage.py" ]; then
    echo "ERRO: manage.py não encontrado em $APP_DIR"
    echo "Clone o Projeto-PDV nesse diretório antes de executar este script."
    exit 1
fi

mkdir -p "$HOME/virtualenvs" "$WEBROOT" "$(dirname "$ENV_FILE")"

if [ ! -x "$VENV_DIR/bin/python" ]; then
    echo "Criando virtualenv..."
    if ! "$PYTHON_BIN" -m venv "$VENV_DIR"; then
        echo "python -m venv não está disponível; tentando virtualenv no usuário..."
        pip3 install --user virtualenv
        "$PYTHON_BIN" -m virtualenv "$VENV_DIR"
    fi
fi

echo "Instalando dependências..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

if [ ! -f "$ENV_FILE" ]; then
    echo "Criando configuração de produção..."
    SECRET_KEY="$("$VENV_DIR/bin/python" -c 'import secrets; print(secrets.token_urlsafe(64))')"
    cat > "$ENV_FILE" <<EOF
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=$SECRET_KEY
DJANGO_ALLOWED_HOSTS=aguiacafe.com.br,www.aguiacafe.com.br
DJANGO_CSRF_TRUSTED_ORIGINS=https://aguiacafe.com.br,https://www.aguiacafe.com.br
DJANGO_STATIC_ROOT=$WEBROOT/static
DJANGO_SECURE_SSL_REDIRECT=False
DJANGO_SECURE_HSTS_SECONDS=0
EOF
    chmod 600 "$ENV_FILE"
fi

set -a
. "$ENV_FILE"
set +a

cd "$APP_DIR"

echo "Executando verificações..."
"$VENV_DIR/bin/python" manage.py check

echo "Aplicando migrations..."
"$VENV_DIR/bin/python" manage.py migrate --noinput

echo "Coletando arquivos estáticos..."
"$VENV_DIR/bin/python" manage.py collectstatic --noinput

cat > "$WEBROOT/.htaccess" <<'EOF'
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteBase /
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteRule ^(.*)$ djangoapp.fcgi/$1 [QSA,L]
</IfModule>
EOF

cat > "$WEBROOT/djangoapp.fcgi" <<EOF
#!$VENV_DIR/bin/python

import os
import sys

APP_DIR = r"$APP_DIR"
ENV_FILE = r"$ENV_FILE"

def load_env(path):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

load_env(ENV_FILE)
sys.path.insert(0, APP_DIR)
os.chdir(APP_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "projeto.settings")

import django
from django.core.handlers.wsgi import WSGIHandler
from flup.server.fcgi import WSGIServer

django.setup(set_prefix=False)
WSGIServer(WSGIHandler()).run()
EOF

chmod 744 "$WEBROOT/djangoapp.fcgi"
chmod 644 "$WEBROOT/.htaccess"

echo
echo "Deploy preparado."
echo "Agora configure no konsoleH o Document Root do domínio para:"
echo "  $WEBROOT"
echo
echo "Depois acesse:"
echo "  https://$DOMAIN"
