## Entrega 2 - Sistema inicial e prova da falha

Objetivo: rodar apenas o Flask, sem coordenador, para mostrar condição de corrida.

Terminal 1:

```bash
cd servico-agendamento
python -m venv venv
# Windows PowerShell: .\venv\Scripts\Activate.ps1
# Git Bash: source venv/Scripts/activate
pip install -r requirements.txt
set USE_COORDINATOR=false
python app.py
```

No Git Bash/Linux/macOS, use:

```bash
USE_COORDINATOR=false python app.py
```

Terminal 2, na raiz do projeto:

```bash
python teste_estresse.py
```

Resultado esperado da Entrega 2: várias requisições `201 Created` e múltiplos agendamentos para o mesmo horário. O arquivo `servico-agendamento/app.log` deve mostrar logs de aplicação entrelaçados e múltiplos eventos de auditoria `AGENDAMENTO_CRIADO` para o mesmo recurso.

## Entrega 3 - Coordenador de lock

Objetivo: rodar Flask + Node.js e provar exclusão mútua.

Terminal 1:

```bash
cd servico-coordenador
npm install
npm start
```

Terminal 2:

```bash
cd servico-agendamento
# com a venv ativada e dependências instaladas
set USE_COORDINATOR=true
set COORDINATOR_URL=http://127.0.0.1:3000
python app.py
```

No Git Bash/Linux/macOS:

```bash
USE_COORDINATOR=true COORDINATOR_URL=http://127.0.0.1:3000 python app.py
```

Terminal 3, na raiz do projeto:

```bash
python teste_estresse.py
```

Resultado esperado da Entrega 3: uma requisição `201 Created` e nove `409 Conflict`. O banco deve conter apenas um agendamento confirmado para o horário testado. O terminal do Node.js deve exibir um lock concedido/liberado e múltiplos locks negados. O `app.log` deve conter apenas um `AGENDAMENTO_CRIADO` para o recurso.

## Entrega 4 - `/time`, cliente inteligente e HATEOAS

Com o Flask rodando, acesse:

```text
http://127.0.0.1:5000/
```

Na tela:

1. Clique em **Sincronizar com o servidor**.
2. Crie um agendamento.
3. Clique em **Cancelar último agendamento via HATEOAS**.

Resultado esperado: a interface usa `/time` para estimar o offset de relógio e usa o link `_links.cancelar` retornado pela API para cancelar o agendamento. O arquivo `app.log` deve registrar chamada ao `/time` e evento de auditoria `AGENDAMENTO_CANCELADO`.

## Entrega 5 - Docker Compose e logs centralizados

Na raiz do projeto:

```bash
docker-compose up --build
```

Em outro terminal:

```bash
docker-compose logs -f
```

Acesse a interface:

```text
http://127.0.0.1:5000/
```

Ou rode o teste:

```bash
python teste_estresse.py
```

Resultado esperado: os dois serviços sobem via Compose, o Flask conversa com o coordenador usando `http://servico-coordenador:3000`, e os logs dos dois serviços aparecem juntos no `docker-compose logs -f`.

## Arquivos principais adicionados

- `servico-agendamento/app.py`: API Flask, banco SQLite, HATEOAS, `/time`, cancelamento e logs.
- `servico-agendamento/static/index.html`: cliente web da Entrega 4.
- `servico-coordenador/server.js`: serviço Node.js com `/lock` e `/unlock`.
- `teste_estresse.py`: teste simultâneo com 10 threads.
- `servico-agendamento/Dockerfile`
- `servico-coordenador/Dockerfile`
- `docker-compose.yml`

## Observação para o vídeo

Para o vídeo, grave três evidências:

1. Entrega 2: teste sem coordenador gerando vários `201` para o mesmo horário.
2. Entrega 3: teste com coordenador gerando um `201` e nove `409`.
3. Entrega 4/5: interface web, cancelamento via HATEOAS e `docker-compose logs -f` mostrando logs dos dois serviços.