#!/bin/sh
set -eu

DOMAIN="${DOMAIN:-aguiacafe.com.br}"
APP_DIR="${APP_DIR:-$HOME/djangoprojects/Projeto-PDV}"
VENV_DIR="${VENV_DIR:-$HOME/virtualenvs/aguiacafe}"
WEBROOT="${WEBROOT:-$HOME/public_html/$DOMAIN}"
ENV_FILE="${ENV_FILE:-$HOME/.config/aguiacafe.env}"
BRANCH="${BRANCH:-feature/clientes-fiado-vendas}"

cd "$APP_DIR"

echo "Atualizando código..."
git fetch origin
git switch "$BRANCH"
git pull --ff-only origin "$BRANCH"

echo "Atualizando dependências..."
"$VENV_DIR/bin/pip" install -r requirements.txt

set -a
. "$ENV_FILE"
set +a

echo "Aplicando migrations..."
"$VENV_DIR/bin/python" manage.py migrate --noinput

echo "Atualizando arquivos estáticos..."
"$VENV_DIR/bin/python" manage.py collectstatic --noinput

echo "Validando Django..."
"$VENV_DIR/bin/python" manage.py check

# Alterar o mtime do script ajuda o FastCGI a perceber uma nova versão.
touch "$WEBROOT/djangoapp.fcgi"

echo "Atualização concluída."
