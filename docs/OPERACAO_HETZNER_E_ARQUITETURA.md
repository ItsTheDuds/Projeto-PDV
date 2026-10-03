# Operação Hetzner, arquitetura do sistema e banco de dados

> Documento operacional do **Águia Café Gestão / Projeto-PDV**.
>
> Ambiente atual: Hetzner **Webhosting L**, executando Django via **CGI**. Apesar de às vezes ser chamado de VPS no dia a dia, este ambiente não usa `systemd`/Gunicorn como uma VPS tradicional.

## 1. Estrutura do servidor

Principais caminhos do ambiente atual:

```text
~/djangoprojects/Projeto-PDV        # código da aplicação
~/virtualenvs/aguiacafe             # ambiente virtual Python
~/.config/aguiacafe.env             # variáveis de ambiente da produção
~/public_html                       # raiz pública do domínio
~/public_html/djangoapp.cgi         # ponto de entrada CGI
~/public_html/static                # arquivos estáticos publicados
~/backups/aguiacafe                 # backups PostgreSQL
```

Host SSH atual:

```text
Host: www781.your-server.de
Porta SSH: 222
Usuário: e667ey
```

Conexão:

```bash
ssh -p 222 e667ey@www781.your-server.de
```

## 2. Regras importantes do ambiente

1. O site em produção usa PostgreSQL quando as variáveis do arquivo `~/.config/aguiacafe.env` são carregadas.
2. Se comandos Django forem executados sem carregar esse arquivo, o projeto pode cair no SQLite local `db.sqlite3`.
3. Não existe reinício por `systemctl` neste ambiente.
4. O recarregamento da aplicação é feito atualizando o arquivo CGI, normalmente com:

```bash
touch ~/public_html/djangoapp.cgi
```

5. O script oficial de atualização já executa esse recarregamento.
6. Nunca imprimir ou compartilhar o conteúdo completo de `~/.config/aguiacafe.env`, pois ele contém credenciais.

## 3. Preparar o shell para comandos Django em produção

Antes de executar comandos manuais que dependem do banco de produção:

```bash
cd ~/djangoprojects/Projeto-PDV

source ~/virtualenvs/aguiacafe/bin/activate

set -a
. ~/.config/aguiacafe.env
set +a
```

Validar qual banco o Django está usando:

```bash
python manage.py shell -c "from django.db import connection; print(connection.settings_dict.get('ENGINE')); print(connection.settings_dict.get('NAME')); print(connection.settings_dict.get('HOST'))"
```

Em produção, o esperado é PostgreSQL.

## 4. Atualização da aplicação

Fluxo normal:

```bash
cd ~/djangoprojects/Projeto-PDV
sh deploy/hetzner/update.sh
```

O script executa, nesta ordem:

```text
git fetch
git switch feature/clientes-fiado-vendas
git pull --ff-only
pip install -r requirements.txt
carrega ~/.config/aguiacafe.env
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py check
touch ~/public_html/djangoapp.cgi
```

Antes de atualizar, é útil verificar se há alterações locais:

```bash
cd ~/djangoprojects/Projeto-PDV
git status
git branch --show-current
git log -5 --oneline
```

Se existir arquivo alterado manualmente no servidor, não usar `git reset --hard` sem revisar. Um arquivo local modificado pode impedir o `git pull --ff-only`.

## 5. Git: comandos operacionais

Atualizar referências remotas:

```bash
git fetch origin
```

Trocar para a branch da aplicação:

```bash
git switch feature/clientes-fiado-vendas
```

Atualizar somente se for possível avançar sem merge:

```bash
git pull --ff-only origin feature/clientes-fiado-vendas
```

Ver modificações locais:

```bash
git status
```

Ver os últimos commits:

```bash
git log -10 --oneline
```

Restaurar **um arquivo conhecido** para a versão do Git:

```bash
git restore caminho/do/arquivo
```

Evitar restaurações destrutivas em massa sem confirmar o que será perdido.

## 6. Django: comandos principais

Verificar configuração:

```bash
python manage.py check
```

Ver migrations:

```bash
python manage.py showmigrations
```

Aplicar migrations:

```bash
python manage.py migrate
```

Coletar arquivos estáticos:

```bash
python manage.py collectstatic --noinput
```

Abrir shell do Django:

```bash
python manage.py shell
```

Executar uma expressão rápida:

```bash
python manage.py shell -c "from vendas.models import Venda; print(Venda.objects.count())"
```

Observação: no PostgreSQL da hospedagem atual, o usuário do banco pode não ter permissão para criar banco temporário. Por isso `python manage.py test` pode falhar antes mesmo dos testes ao tentar criar o banco de testes. Prefira rodar a suíte completa em ambiente local/CI.

## 7. Backup PostgreSQL

Script:

```text
deploy/hetzner/backup_postgres.sh
```

Criar backup manual imediatamente:

```bash
cd ~/djangoprojects/Projeto-PDV

source ~/virtualenvs/aguiacafe/bin/activate
set -a
. ~/.config/aguiacafe.env
set +a

FORCE_BACKUP=1 sh deploy/hetzner/backup_postgres.sh
```

Os arquivos são gravados por padrão em:

```text
~/backups/aguiacafe/
```

Formato de nome:

```text
aguiacafe_YYYY-MM-DD_HHhMMmSS_Brasilia.dump
```

Listar backups:

```bash
ls -lh ~/backups/aguiacafe
```

Validar a estrutura de um dump sem restaurar:

```bash
pg_restore --list ~/backups/aguiacafe/NOME_DO_BACKUP.dump | head
```

O script:
- usa `pg_dump --format=custom`;
- grava sem owner e sem ACL;
- valida o dump com `pg_restore --list` quando disponível;
- remove backups mais antigos que o período configurado;
- usa, por padrão, retenção de 30 dias;
- considera o fuso `America/Sao_Paulo`.

Para conferir o cron:

```bash
crontab -l
```

A configuração adotada pode executar o script a cada hora, enquanto o próprio script só efetiva o backup no horário configurado para Brasília, salvo quando `FORCE_BACKUP=1`.

## 8. Variáveis de ambiente

Arquivo:

```text
~/.config/aguiacafe.env
```

Editar:

```bash
nano ~/.config/aguiacafe.env
```

Variáveis principais utilizadas pelo projeto:

```text
DJANGO_DEBUG
DJANGO_SECRET_KEY
DJANGO_ALLOWED_HOSTS
DJANGO_CSRF_TRUSTED_ORIGINS
DJANGO_DB_ENGINE

DB_NAME
DB_USER
DB_PASSWORD
DB_HOST
DB_PORT
DB_SSLMODE

DJANGO_ADMIN_URL
DJANGO_STATIC_ROOT
DJANGO_SECURE_SSL_REDIRECT
DJANGO_SECURE_HSTS_SECONDS
```

Nunca versionar esse arquivo no Git.

## 9. Arquitetura da aplicação

Apps Django principais:

```text
clientes/
produtos/
vendas/
fiado/
projeto/
templates/
deploy/hetzner/
```

Responsabilidades:

### `clientes`
Cadastro de clientes e cálculo do saldo devedor.

### `produtos`
Cadastro de produtos e preços.

A versão Águia Café não utiliza controle de estoque.

### `vendas`
PDV, carrinho, itens vendidos, histórico, comprovante e totalização de vendas.

No momento, a forma de pagamento operacional desta branch é `FIADO`.

### `fiado`
Controle de dívida, pagamento parcial, quitação, histórico de recebimentos e senha de quitação.

### `projeto`
Configuração Django, URLs principais, autenticação e settings.

## 10. Estrutura lógica do banco de dados

Além das tabelas internas do Django (`auth_*`, `django_*`, sessões etc.), as tabelas de negócio são derivadas dos models abaixo.

### Cliente — `clientes_cliente`

```text
id
nome              varchar(120)
celular           varchar(11), indexado
email             email, opcional
criado_em         datetime
```

Relacionamentos:
- 1 Cliente → N Vendas
- 1 Cliente → N RecebimentosFiado

O celular é normalizado para 11 dígitos.

### Produto — `produtos_produtosmodel`

```text
id
nome              varchar(100)
descricao         text, opcional
preco             decimal(10,2)
```

Não existe campo de estoque nesta branch.

### Venda — `vendas_venda`

```text
id
cliente_id        FK Cliente, opcional, PROTECT
forma_pagamento   varchar(20)
total             decimal(12,2)
criada_em         datetime
```

Na operação atual:

```text
forma_pagamento = FIADO
```

Relacionamentos:
- N Vendas → 1 Cliente
- 1 Venda → N ItemVenda
- 1 Venda → 1 Fiado quando a venda é fiada

### ItemVenda — `vendas_itemvenda`

```text
id
venda_id          FK Venda, CASCADE
produto_id        FK Produto, PROTECT
quantidade        inteiro positivo
preco_unitario    decimal(10,2)
subtotal          decimal(12,2)
```

Importante: `quantidade` aqui significa **quantidade vendida**, não estoque.

### Fiado — `fiado_fiado`

```text
id
venda_id          OneToOne Venda, CASCADE
pago              boolean, indexado
valor_pago        decimal(12,2)
pago_em           datetime, opcional
```

Saldo calculado:

```text
saldo_devedor = venda.total - valor_pago
```

Estados típicos:

```text
valor_pago = 0                 -> em aberto
0 < valor_pago < venda.total  -> parcial
valor_pago = venda.total       -> pago
```

### RecebimentoFiado — `fiado_recebimentofiado`

Representa uma operação de recebimento feita pelo operador.

```text
id
cliente_id        FK Cliente, PROTECT
valor_total       decimal(12,2)
usuario_id        FK usuário Django, SET_NULL
criado_em         datetime
```

Um único recebimento pode quitar várias vendas antigas.

### AplicacaoRecebimento — `fiado_aplicacaorecebimento`

Mostra como um recebimento foi distribuído entre as dívidas.

```text
id
recebimento_id    FK RecebimentoFiado, CASCADE
fiado_id          FK Fiado, PROTECT
valor             decimal(12,2)
```

Exemplo:

```text
Recebimento do cliente: R$ 100,00
  -> Venda #10: R$ 30,00
  -> Venda #11: R$ 50,00
  -> Venda #12: R$ 20,00
```

A aplicação é feita nas dívidas mais antigas primeiro.

### ConfiguracaoFiado — `fiado_configuracaofiado`

```text
id
senha_hash        varchar(128)
atualizado_em     datetime
```

A senha é armazenada com hash do Django, nunca em texto puro.

A aplicação utiliza um único registro de configuração, normalmente com `pk=1`.

## 11. Diagrama simplificado

```text
Cliente
  |
  +----< Venda >---- Produto
  |        |
  |        +----< ItemVenda
  |
  |        1
  |        |
  |       Fiado
  |        ^
  |        |
  +----< RecebimentoFiado
             |
             +----< AplicacaoRecebimento >---- Fiado
```

Em termos práticos:

```text
Cliente
  -> faz uma Venda
      -> contém ItemVenda
      -> se for FIADO, cria um Fiado

Cliente
  -> realiza um RecebimentoFiado
      -> o valor é distribuído em AplicacaoRecebimento
      -> cada aplicação reduz o saldo de um Fiado
```

## 12. Usuários e permissões

O projeto usa autenticação nativa do Django.

### Usuário comum / operador

Pode operar o sistema conforme as telas liberadas.

A senha inicial de quitação do fiado pode ser cadastrada quando ainda não existe configuração.

Depois de configurada, um usuário comum não pode resetar essa senha.

### SuperUser

Definido pelo campo `is_superuser=True` do Django Admin.

Possui permissões administrativas adicionais, incluindo:
- reset da senha de quitação;
- acesso ao painel de total de vendas por período na tela de Fiados;
- acesso ao endpoint do resumo de vendas.

O backend também bloqueia o endpoint de resumo para não-SuperUsers, portanto esconder o painel no HTML não é a única proteção.

## 13. Consultas úteis pelo Django shell

Quantidade de clientes:

```bash
python manage.py shell -c "from clientes.models import Cliente; print(Cliente.objects.count())"
```

Quantidade de produtos:

```bash
python manage.py shell -c "from produtos.models import produtosModel; print(produtosModel.objects.count())"
```

Quantidade de vendas:

```bash
python manage.py shell -c "from vendas.models import Venda; print(Venda.objects.count())"
```

Fiados em aberto:

```bash
python manage.py shell -c "from fiado.models import Fiado; print(Fiado.objects.filter(pago=False).count())"
```

Recebimentos registrados:

```bash
python manage.py shell -c "from fiado.models import RecebimentoFiado; print(RecebimentoFiado.objects.count())"
```

Ver os campos atuais de Produto:

```bash
python manage.py shell -c "from produtos.models import produtosModel; print([f.name for f in produtosModel._meta.fields])"
```

## 14. Procedimento recomendado antes de deploy importante

```text
1. Confirmar que ninguém está finalizando venda/recebimento naquele instante.
2. Criar backup PostgreSQL forçado.
3. Verificar git status.
4. Executar deploy/hetzner/update.sh.
5. Confirmar "Atualização concluída."
6. Fazer login.
7. Testar PDV.
8. Testar Fiado.
9. Testar Clientes e Produtos.
10. Conferir um recebimento sem alterar dados reais indevidamente.
```

Comandos:

```bash
cd ~/djangoprojects/Projeto-PDV

source ~/virtualenvs/aguiacafe/bin/activate
set -a
. ~/.config/aguiacafe.env
set +a

FORCE_BACKUP=1 sh deploy/hetzner/backup_postgres.sh

git status

sh deploy/hetzner/update.sh
```

## 15. Comandos que exigem cuidado

Não executar sem saber exatamente o impacto:

```text
git reset --hard
git clean -fd
DROP DATABASE
TRUNCATE
DELETE sem filtro
flush do Django
restauração de dump diretamente sobre produção
alteração manual de migrations já aplicadas
```

Antes de qualquer operação destrutiva, criar backup e confirmar o banco conectado.
