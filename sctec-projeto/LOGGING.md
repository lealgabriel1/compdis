# SCTEC - Entrega 1: Design de Logging

**Sistema:** Sistema de Controle de Telescópio Espacial Compartilhado (SCTEC)  
**Entrega:** 1 - Definições da API  
**Objetivo:** definir o padrão de logs de aplicação e logs de auditoria do sistema.

---

## 1. Finalidade dos logs

O SCTEC precisa registrar eventos para dois fins diferentes:

1. **Logs de aplicação:** ajudam na depuração técnica e no entendimento do fluxo do sistema.
2. **Logs de auditoria:** registram eventos relevantes do negócio de forma rastreável, permitindo reconstruir o que ocorreu em caso de falha, disputa ou contestação de agendamento.

---

## 2. Logs de aplicação

Logs de aplicação são mensagens técnicas emitidas pelos serviços durante a execução. Eles podem ser usados para depuração, monitoramento e análise de concorrência.

### 2.1 Formato textual proposto

```text
LEVEL:timestamp_utc:service:request_id:message
```

### 2.2 Exemplo

```text
INFO:2025-10-26T18:00:04.500Z:servico-agendamento:req-20251026-000123:Requisição recebida para POST /agendamentos
INFO:2025-10-26T18:00:04.505Z:servico-agendamento:req-20251026-000123:Tentando adquirir lock para o recurso Hubble-Acad_2025-12-01T03:00:00Z
INFO:2025-10-26T18:00:05.120Z:servico-agendamento:req-20251026-000123:Lock adquirido com sucesso
INFO:2025-10-26T18:00:05.122Z:servico-agendamento:req-20251026-000123:Iniciando verificação de conflito no BD
INFO:2025-10-26T18:00:05.123Z:servico-agendamento:req-20251026-000123:Salvando novo agendamento no BD
```

### 2.3 Pontos mínimos de log no serviço Flask

| Momento | Mensagem sugerida |
|---|---|
| Recebimento de requisição | `Requisição recebida para POST /agendamentos` |
| Antes da verificação no banco | `Iniciando verificação de conflito no BD` |
| Antes da persistência | `Salvando novo agendamento no BD` |
| Antes de pedir lock | `Tentando adquirir lock para o recurso X` |
| Lock concedido | `Lock adquirido com sucesso para o recurso X` |
| Lock negado | `Falha ao adquirir lock para o recurso X, recurso ocupado` |
| Antes de liberar lock | `Liberando lock para o recurso X` |
| Consulta de tempo | `Requisição recebida em GET /time` |

### 2.4 Pontos mínimos de log no serviço Node.js

| Momento | Mensagem sugerida |
|---|---|
| Pedido de lock recebido | `Recebido pedido de lock para recurso X` |
| Lock concedido | `Lock concedido para recurso X` |
| Lock negado | `Recurso X já está em uso, negando lock` |
| Pedido de unlock recebido | `Recebido pedido de unlock para recurso X` |
| Lock liberado | `Lock para recurso X liberado` |

---

## 3. Logs de auditoria

Logs de auditoria são eventos de negócio estruturados em JSON. Eles devem ser tratados como registros imutáveis.

### 3.1 Estrutura padrão

```json
{
  "timestamp_utc": "2025-10-26T18:00:05.123Z",
  "level": "AUDIT",
  "event_type": "AGENDAMENTO_CRIADO",
  "service": "servico-agendamento",
  "request_id": "req-20251026-000123",
  "actor": {
    "type": "CIENTISTA",
    "cientista_id": 7,
    "nome": "Marie Curie"
  },
  "details": {
    "agendamento_id": 123,
    "cientista_id": 7,
    "telescopio_id": 1,
    "recurso_lock": "Hubble-Acad_2025-12-01T03:00:00Z",
    "horario_inicio_utc": "2025-12-01T03:00:00Z",
    "horario_fim_utc": "2025-12-01T03:05:00Z",
    "status": "CONFIRMADO"
  }
}
```

---

## 4. Campos obrigatórios do log de auditoria

| Campo | Obrigatório | Justificativa |
|---|:---:|---|
| `timestamp_utc` | sim | Permite reconstruir a ordem dos eventos. |
| `level` | sim | Distingue logs de auditoria de logs comuns. |
| `event_type` | sim | Classifica o evento de negócio. |
| `service` | sim | Indica qual serviço produziu o registro. |
| `request_id` | sim | Permite correlacionar logs da mesma requisição. |
| `actor` | sim | Identifica quem executou a ação. |
| `details` | sim | Armazena os dados específicos do evento. |

---

## 5. Tipos de evento de auditoria

### 5.1 `AGENDAMENTO_CRIADO`

Emitido quando um agendamento é confirmado e salvo no banco.

```json
{
  "timestamp_utc": "2025-10-26T18:00:05.123Z",
  "level": "AUDIT",
  "event_type": "AGENDAMENTO_CRIADO",
  "service": "servico-agendamento",
  "request_id": "req-20251026-000123",
  "actor": {
    "type": "CIENTISTA",
    "cientista_id": 7,
    "nome": "Marie Curie"
  },
  "details": {
    "agendamento_id": 123,
    "telescopio_id": 1,
    "recurso_lock": "Hubble-Acad_2025-12-01T03:00:00Z",
    "horario_inicio_utc": "2025-12-01T03:00:00Z",
    "horario_fim_utc": "2025-12-01T03:05:00Z",
    "status": "CONFIRMADO"
  }
}
```

### 5.2 `AGENDAMENTO_CANCELADO`

Emitido quando um agendamento confirmado é cancelado.

```json
{
  "timestamp_utc": "2025-10-26T19:15:00.000Z",
  "level": "AUDIT",
  "event_type": "AGENDAMENTO_CANCELADO",
  "service": "servico-agendamento",
  "request_id": "req-20251026-000200",
  "actor": {
    "type": "CIENTISTA",
    "cientista_id": 7,
    "nome": "Marie Curie"
  },
  "details": {
    "agendamento_id": 123,
    "status_anterior": "CONFIRMADO",
    "status_atual": "CANCELADO",
    "motivo": "Cancelamento solicitado pelo cientista responsável."
  }
}
```

### 5.3 `AGENDAMENTO_REJEITADO_CONFLITO`

Emitido quando uma tentativa de agendamento é rejeitada por conflito de horário ou recurso bloqueado.

```json
{
  "timestamp_utc": "2025-10-26T18:00:05.121Z",
  "level": "AUDIT",
  "event_type": "AGENDAMENTO_REJEITADO_CONFLITO",
  "service": "servico-agendamento",
  "request_id": "req-20251026-000124",
  "actor": {
    "type": "CIENTISTA",
    "cientista_id": 8,
    "nome": "Albert Einstein"
  },
  "details": {
    "telescopio_id": 1,
    "recurso_lock": "Hubble-Acad_2025-12-01T03:00:00Z",
    "horario_inicio_utc": "2025-12-01T03:00:00Z",
    "motivo": "Recurso ocupado ou conflito com agendamento existente."
  }
}
```

---

## 6. Correlação entre serviços

O campo `request_id` deve ser repassado do serviço Flask para o serviço Node.js quando o Flask solicitar lock ou unlock. Isso permite rastrear a mesma operação nos logs dos dois serviços.

### Exemplo de fluxo correlacionado

```text
INFO:2025-10-26T18:00:04.500Z:servico-agendamento:req-20251026-000123:Requisição recebida para POST /agendamentos
INFO:2025-10-26T18:00:04.505Z:servico-agendamento:req-20251026-000123:Tentando adquirir lock para o recurso Hubble-Acad_2025-12-01T03:00:00Z
INFO:2025-10-26T18:00:04.510Z:servico-coordenador:req-20251026-000123:Recebido pedido de lock para recurso Hubble-Acad_2025-12-01T03:00:00Z
INFO:2025-10-26T18:00:04.511Z:servico-coordenador:req-20251026-000123:Lock concedido para recurso Hubble-Acad_2025-12-01T03:00:00Z
AUDIT:{"timestamp_utc":"2025-10-26T18:00:05.123Z","level":"AUDIT","event_type":"AGENDAMENTO_CRIADO","service":"servico-agendamento","request_id":"req-20251026-000123"}
INFO:2025-10-26T18:00:05.130Z:servico-agendamento:req-20251026-000123:Liberando lock para o recurso Hubble-Acad_2025-12-01T03:00:00Z
```

---

## 7. Política de armazenamento

Na implementação inicial, os logs podem ser gravados em arquivo local `app.log` e exibidos no console. Em etapas futuras, os logs poderão ser centralizados via Docker Compose e ferramentas de observabilidade.

### Arquivos previstos

| Serviço | Arquivo de log sugerido |
|---|---|
| `servico-agendamento` | `app.log` |
| `servico-coordenador` | console padrão do Node.js |

---

## 8. Requisitos de qualidade dos logs

1. Logs de auditoria devem ser estruturados em JSON.
2. Logs de auditoria não devem ser editados manualmente.
3. Todas as datas devem estar em UTC.
4. Cada requisição deve possuir `request_id`.
5. Eventos críticos devem conter o identificador do cientista, do agendamento, do telescópio e do recurso de lock quando aplicável.
6. Em caso de conflito, o sistema deve registrar tanto a tentativa quanto o motivo da rejeição.
