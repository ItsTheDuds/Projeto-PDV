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
