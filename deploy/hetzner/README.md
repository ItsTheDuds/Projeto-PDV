# Deploy do Águia Café na Hetzner Webhosting L

Este diretório contém os scripts usados para publicar o Projeto-PDV no Webhosting L.

Na conta atual, o domínio `aguiacafe.com.br` usa diretamente `$HOME/public_html` como Document Root. O deploy usa CGI com Python, que é suportado pela Hetzner Webhosting.

## Estrutura esperada

```text
$HOME/
├── djangoprojects/
│   └── Projeto-PDV/
├── virtualenvs/
│   └── aguiacafe/
├── .config/
│   └── aguiacafe.env
└── public_html/
    ├── .htaccess
    ├── djangoapp.cgi
    └── static/
```

## Instalação

Depois de clonar o projeto:

```bash
cd ~/djangoprojects/Projeto-PDV
sh deploy/hetzner/install.sh
```

O script cria ou atualiza o virtualenv, instala as dependências, aplica migrations, coleta os arquivos estáticos e cria `.htaccess` e `djangoapp.cgi` diretamente em `$HOME/public_html`.

## HTTPS

Mantenha inicialmente:

```text
DJANGO_SECURE_SSL_REDIRECT=False
DJANGO_SECURE_HSTS_SECONDS=0
```

Use apenas uma camada de redirecionamento HTTP → HTTPS. Não habilite HSTS antes de confirmar que HTTPS está estável.

## Atualizações futuras

```bash
cd ~/djangoprojects/Projeto-PDV
sh deploy/hetzner/update.sh
```

Por padrão, o script atualiza a branch `feature/clientes-fiado-vendas`. Depois que ela for incorporada na `main`:

```bash
BRANCH=main sh deploy/hetzner/update.sh
```

## Banco de dados

A aplicação continua usando SQLite nesta primeira versão. Faça backups regulares do arquivo do banco antes de atualizações importantes.

## PostgreSQL

Em produção, configure o arquivo `~/.config/aguiacafe.env` com:

```text
DJANGO_DB_ENGINE=postgresql
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_HOST=...
DB_PORT=5432
```

O hostname deve ser o fornecido pelo konsoleH; não use `localhost`.

Se a opção **Require SSL** for habilitada na criação do banco, acrescente:

```text
DB_SSLMODE=require
```

Depois instale as dependências e aplique as migrations:

```bash
cd ~/djangoprojects/Projeto-PDV
~/virtualenvs/aguiacafe/bin/pip install -r requirements.txt
set -a
. ~/.config/aguiacafe.env
set +a
~/virtualenvs/aguiacafe/bin/python manage.py check
~/virtualenvs/aguiacafe/bin/python manage.py migrate
```

Como o banco PostgreSQL começa vazio, crie o usuário administrativo novamente:

```bash
~/virtualenvs/aguiacafe/bin/python manage.py createsuperuser
```

## Backup PostgreSQL

O script `deploy/hetzner/backup_postgres.sh` cria backups no formato custom do PostgreSQL e mantém 30 dias por padrão.

O horário do backup é controlado pelo próprio script usando o fuso `America/Sao_Paulo`. Por padrão, ele executa o backup às **02:00 de Brasília**, independentemente do horário CET/CEST da Hetzner.

No Cron Job Manager da Hetzner, configure o script para ser chamado **uma vez por hora**, no minuto zero:

```text
00 * * * *
```

Nas demais horas, o script encerra normalmente sem criar backup.

Teste manual, ignorando o horário programado:

```bash
FORCE_BACKUP=1 sh deploy/hetzner/backup_postgres.sh
```

Para escolher outro horário de Brasília, por exemplo 03:00:

```text
BACKUP_HOUR_BRASILIA=03
```

Essa variável pode ser adicionada ao arquivo `~/.config/aguiacafe.env`.

Para alterar a retenção:

```bash
BACKUP_RETENTION_DAYS=60 sh deploy/hetzner/backup_postgres.sh
```

Os arquivos ficam em:

```text
$HOME/backups/aguiacafe/
```

Cadastre o script no Cron Job Manager somente depois de confirmar que o backup manual funciona.
