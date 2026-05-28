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