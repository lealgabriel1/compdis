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