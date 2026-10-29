# Recuperação do Projeto PDV — PostgreSQL + Django

Este guia explica como restaurar o banco de dados PostgreSQL a partir de um backup `.dump` e executar a aplicação Django localmente no Windows.

## 1. Instalar o PostgreSQL

1. Acesse https://www.postgresql.org/download/windows/
2. Baixe e instale o PostgreSQL.
3. Durante a instalação, defina uma senha para o usuário `postgres`.
4. Mantenha a porta padrão `5432`.
5. Adicione a pasta `bin` do PostgreSQL às variáveis de ambiente `Path` do Windows.

Exemplo de caminho:

```text
C:\Program Files\PostgreSQL\17\bin
```

Abra um novo PowerShell e verifique:

```powershell
psql --version
pg_restore --version
```

## 2. Preparar o backup

Baixe o arquivo `.dump` da VPS e salve na pasta `Downloads`.

Verifique se o backup é reconhecido:

```powershell
pg_restore -l "C:\CAMINHO\backup.dump"
```

Se aparecer uma lista de tabelas e objetos do banco, podemos continuar.

**Atenção:** confirme que o arquivo não está vazio (0 bytes).

## 3. Criar o banco PostgreSQL

No PowerShell, execute:

```powershell
createdb -U postgres -h localhost -p 5432 -T template0 db_aguiacafe
```

Digite a senha do PostgreSQL.

Isso criará o banco vazio `db_aguiacafe`.

## 4. Restaurar o backup

Execute:

```powershell
pg_restore -U postgres -h localhost -p 5432 -d db_aguiacafe --no-owner --no-acl --exit-on-error -v "C:\CAMINHO\backup.dump"
```

Substitua `C:\CAMINHO\backup.dump` pelo caminho do backup correto.

Esse comando deve ser executado com o banco vazio.

Para conferir as tabelas restauradas:

```powershell
psql -U postgres -h localhost -d db_aguiacafe
```

Dentro do PostgreSQL:

```sql
\dt
```

Para sair:

```sql
\q
```

## 5. Preparar o Django

Abra o PowerShell na pasta do projeto:

```powershell
cd "C:\Users\miguel.ferreira\Documents\Projeto-PDV"
```

Crie o ambiente virtual, caso ainda não exista:

```powershell
python -m venv .venv
```

Ative:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

## 6. Configurar a conexão com o banco

No mesmo PowerShell, execute:

```powershell
$env:DJANGO_DB_ENGINE = "postgresql"
$env:DB_NAME = "db_aguiacafe"
$env:DB_USER = "postgres"
$env:DB_HOST = "127.0.0.1"
$env:DB_PORT = "5432"
$env:DB_SSLMODE = "disable"
```

Configure a senha do PostgreSQL:

```powershell
$senha = Read-Host "Senha do PostgreSQL" -AsSecureString
$env:DB_PASSWORD = [System.Net.NetworkCredential]::new("", $senha).Password
```

**Importante:** essas variáveis são temporárias. Se fechar o PowerShell, será necessário configurá-las novamente.

Não coloque senhas reais no GitHub.

## 7. Testar a conexão do Django

Verifique se o Django está utilizando PostgreSQL:

```powershell
python manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default']['ENGINE']); print(settings.DATABASES['default']['NAME'])"
```

Resultado esperado:

```text
django.db.backends.postgresql
db_aguiacafe
```

Teste a conexão:

```powershell
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('PostgreSQL conectado com sucesso!')"
```

## 8. Verificar as migrações

Execute:

```powershell
python manage.py showmigrations
python manage.py migrate --plan
python manage.py check
```

Não execute `migrate` automaticamente em um banco restaurado sem verificar se as migrações são compatíveis com a versão do projeto.

## 9. Iniciar o Django

Execute:

```powershell
python manage.py runserver 127.0.0.1:8000
```

Acesse no navegador:

http://127.0.0.1:8000

Se houver Django Admin:

http://127.0.0.1:8000/admin/

Verifique se o sistema abre normalmente e se os dados do backup estão disponíveis.

## 10. Checklist final

- [ ] PostgreSQL instalado
- [ ] Backup `.dump` verificado
- [ ] Banco `db_aguiacafe` criado
- [ ] Backup restaurado
- [ ] Ambiente virtual do Django ativado
- [ ] Dependências instaladas
- [ ] Variáveis de ambiente configuradas
- [ ] Conexão Django/PostgreSQL funcionando
- [ ] Migrações verificadas
- [ ] Aplicação iniciando sem erros
- [ ] Login e principais funcionalidades testados

---

**Observações**

- Esse procedimento foi testado no Windows utilizando PowerShell.
- O backup contém os dados até a data em que foi gerado.
- Arquivos enviados pelos usuários (pasta `media/`) precisam de backup separado, caso existam.
- Para recuperar o sistema em outra VPS, também será necessário configurar o servidor web, o serviço Django, as variáveis de produção e o HTTPS.
- O comando `runserver` é destinado apenas ao ambiente local, não à produção.

**Resultado:** procedimento de restauração do PostgreSQL e inicialização local do Django validado com sucesso.
