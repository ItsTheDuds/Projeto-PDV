#!/bin/sh
set -eu

ENV_FILE="${ENV_FILE:-$HOME/.config/aguiacafe.env}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/aguiacafe}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
BACKUP_TIMEZONE="${BACKUP_TIMEZONE:-America/Sao_Paulo}"
BACKUP_HOUR_BRASILIA="${BACKUP_HOUR_BRASILIA:-02}"
FORCE_BACKUP="${FORCE_BACKUP:-0}"

case "$BACKUP_HOUR_BRASILIA" in
    00|01|02|03|04|05|06|07|08|09|10|11|12|13|14|15|16|17|18|19|20|21|22|23) ;;
    *)
        echo "ERRO: BACKUP_HOUR_BRASILIA deve estar entre 00 e 23." >&2
        exit 1
        ;;
esac

HORA_BRASILIA="$(TZ="$BACKUP_TIMEZONE" date +%H)"
AGORA_BRASILIA="$(TZ="$BACKUP_TIMEZONE" date '+%Y-%m-%d %H:%M:%S %Z')"

if [ "$FORCE_BACKUP" != "1" ] && [ "$HORA_BRASILIA" != "$BACKUP_HOUR_BRASILIA" ]; then
    echo "Backup não executado. Agora em Brasília: $AGORA_BRASILIA. Horário programado: ${BACKUP_HOUR_BRASILIA}:00."
    exit 0
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "ERRO: arquivo de ambiente não encontrado em $ENV_FILE" >&2
    exit 1
fi

set -a
. "$ENV_FILE"
set +a

if [ "${DJANGO_DB_ENGINE:-}" != "postgresql" ] && [ "${DJANGO_DB_ENGINE:-}" != "postgres" ]; then
    echo "ERRO: DJANGO_DB_ENGINE não está configurado como PostgreSQL." >&2
    exit 1
fi

for var in DB_NAME DB_USER DB_PASSWORD DB_HOST DB_PORT; do
    eval "value=\${$var:-}"
    if [ -z "$value" ]; then
        echo "ERRO: variável $var não definida." >&2
        exit 1
    fi
done

if ! command -v pg_dump >/dev/null 2>&1; then
    echo "ERRO: pg_dump não está disponível neste servidor." >&2
    exit 1
fi

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

STAMP="$(TZ="$BACKUP_TIMEZONE" date +%Y-%m-%d_%Hh%Mm%S)"
DEST="$BACKUP_DIR/aguiacafe_${STAMP}_Brasilia.dump"
TMP="$DEST.tmp"

cleanup() {
    rm -f "$TMP"
}
trap cleanup EXIT HUP INT TERM

echo "Criando backup PostgreSQL... Horário de Brasília: $AGORA_BRASILIA"
PGPASSWORD="$DB_PASSWORD" pg_dump     --host="$DB_HOST"     --port="$DB_PORT"     --username="$DB_USER"     --dbname="$DB_NAME"     --format=custom     --no-owner     --no-acl     --file="$TMP"

if [ ! -s "$TMP" ]; then
    echo "ERRO: backup foi criado vazio." >&2
    exit 1
fi

if command -v pg_restore >/dev/null 2>&1; then
    pg_restore --list "$TMP" >/dev/null
fi

mv "$TMP" "$DEST"
chmod 600 "$DEST"
trap - EXIT HUP INT TERM

find "$BACKUP_DIR"     -type f     -name 'aguiacafe_*.dump'     -mtime "+$BACKUP_RETENTION_DAYS"     -delete

echo "Backup concluído: $DEST"
