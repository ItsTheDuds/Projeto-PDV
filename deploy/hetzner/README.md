# Deploy do Águia Café na Hetzner Webhosting L

Este diretório contém os scripts usados para publicar o Projeto-PDV no Webhosting L.

A arquitetura segue o modelo documentado pela Hetzner:

- projeto Django fora de `public_html`;
- virtualenv separado;
- raiz pública específica para o domínio;
- `.htaccess` usando `mod_rewrite`;
- `djangoapp.fcgi` executando o Django via FastCGI;
- arquivos estáticos coletados diretamente na raiz pública.

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
    └── aguiacafe.com.br/
        ├── .htaccess
        ├── djangoapp.fcgi
        └── static/
```

## 1. Conectar por SSH

A Hetzner Webhosting usa SSH na porta 222.

```bash
ssh -p 222 SEU_USUARIO@SEU_SERVIDOR
```

## 2. Conferir o Python

O Projeto-PDV usa Django 6.0 e requer Python 3.12 ou superior.

```bash
python3 --version
git --version
```

Caso a Hetzner disponibilize uma versão específica, ela pode ser passada ao script:

```bash
PYTHON_BIN=python3.12 sh deploy/hetzner/install.sh
```

## 3. Baixar o projeto

Como o repositório é privado, configure uma chave SSH somente-leitura no GitHub ou faça o upload do projeto por SFTP.

Exemplo depois que a chave estiver autorizada:

```bash
mkdir -p ~/djangoprojects
cd ~/djangoprojects
git clone --branch feature/clientes-fiado-vendas git@github.com:ItsTheDuds/Projeto-PDV.git
cd Projeto-PDV
```

## 4. Instalação

```bash
sh deploy/hetzner/install.sh
```

O script:

1. cria o virtualenv;
2. instala Django e flup;
3. gera uma chave secreta de produção;
4. cria `~/.config/aguiacafe.env` com permissão 600;
5. executa migrations;
6. executa collectstatic;
7. cria `.htaccess`;
8. cria `djangoapp.fcgi`.

## 5. Configurar o domínio no konsoleH

No painel da Hetzner, altere o **Document Root** de `aguiacafe.com.br` para a pasta:

```text
$HOME/public_html/aguiacafe.com.br
```

No painel aparecerá o caminho absoluto da sua conta; use esse caminho, não o texto literal `$HOME`.

## 6. HTTPS

Mantenha inicialmente:

```text
DJANGO_SECURE_SSL_REDIRECT=False
DJANGO_SECURE_HSTS_SECONDS=0
```

Depois que o certificado SSL do domínio estiver ativo e o site abrir corretamente por HTTPS, edite:

```bash
nano ~/.config/aguiacafe.env
```

e altere para:

```text
DJANGO_SECURE_SSL_REDIRECT=True
```

HSTS deve ser habilitado somente depois de confirmar que HTTPS está estável.

## 7. Atualizações futuras

```bash
cd ~/djangoprojects/Projeto-PDV
sh deploy/hetzner/update.sh
```

Por padrão o script atualiza a branch `feature/clientes-fiado-vendas`.
Depois que ela for incorporada na main, use:

```bash
BRANCH=main sh deploy/hetzner/update.sh
```

## Banco de dados

Nesta primeira versão o projeto continua usando SQLite. Para um comércio pequeno e um único processo de aplicação, isso mantém a implantação simples. Se o volume ou concorrência crescerem, o banco pode ser migrado posteriormente para MariaDB/PostgreSQL.
