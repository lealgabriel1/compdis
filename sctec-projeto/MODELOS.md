# SCTEC - Entrega 1: Modelos do Sistema

**Sistema:** Sistema de Controle de Telescópio Espacial Compartilhado (SCTEC)  
**Entrega:** 1 - Definições da API  
**Objetivo:** definir as entidades principais do sistema de agendamento, seus atributos, relacionamentos e regras de negócio iniciais.

---

## 1. Visão geral do domínio

O SCTEC controla o uso compartilhado de um telescópio espacial acadêmico. Cientistas de diferentes instituições solicitam janelas de observação. Como o recurso é caro, escasso e disputado, o sistema precisa registrar agendamentos de forma consistente, rastreável e auditável.

Na Entrega 1, o foco é especificar o contrato da API e os modelos conceituais. A implementação do serviço Flask, a prova de condição de corrida, o serviço coordenador Node.js e a orquestração com Docker ficam para as próximas etapas.

---

## 2. Entidades principais

### 2.1 Cientista

Representa o usuário acadêmico autorizado a solicitar tempo de observação.

| Campo | Tipo | Obrigatório | Descrição |
|---|---:|:---:|---|
| `cientista_id` | inteiro | sim | Identificador único do cientista. |
| `nome` | texto | sim | Nome completo do cientista. |
| `email` | texto | sim | E-mail institucional ou de contato. Deve ser único. |
| `instituicao` | texto | sim | Universidade, instituto ou laboratório de vínculo. |
| `pais` | texto | não | País de origem da instituição. |
| `area_pesquisa` | texto | não | Área científica principal, como astrofísica, cosmologia ou física solar. |
| `criado_em_utc` | datetime UTC | sim | Data e hora de criação do cadastro. |
| `ativo` | booleano | sim | Indica se o cientista pode solicitar agendamentos. |

#### Regras iniciais

- O e-mail do cientista deve ser único.
- Cientistas inativos não podem criar novos agendamentos.
- Um cientista pode possuir vários agendamentos.

#### Exemplo JSON

```json
{
  "cientista_id": 7,
  "nome": "Marie Curie",
  "email": "marie.curie@universidade-paris.fr",
  "instituicao": "Universidade de Paris",
  "pais": "França",
  "area_pesquisa": "Radiação cósmica",
  "criado_em_utc": "2025-10-26T18:00:00Z",
  "ativo": true,
  "_links": {
    "self": { "href": "/cientistas/7", "method": "GET" },
    "agendamentos": { "href": "/cientistas/7/agendamentos", "method": "GET" },
    "criar_agendamento": { "href": "/agendamentos", "method": "POST" }
  }
}
```

---

### 2.2 Telescópio

Representa o recurso físico compartilhado que será reservado.

| Campo | Tipo | Obrigatório | Descrição |
|---|---:|:---:|---|
| `telescopio_id` | inteiro | sim | Identificador único do telescópio. |
| `codigo` | texto | sim | Código curto usado no recurso de lock, por exemplo `Hubble-Acad`. |
| `nome` | texto | sim | Nome do telescópio. |
| `descricao` | texto | não | Descrição operacional ou científica. |
| `status_operacional` | texto | sim | Estado atual: `OPERACIONAL`, `MANUTENCAO`, `INDISPONIVEL`. |
| `criado_em_utc` | datetime UTC | sim | Data e hora de criação do registro. |

#### Regras iniciais

- Apenas telescópios com status `OPERACIONAL` podem receber novos agendamentos.
- O campo `codigo` deve ser único e será usado para compor a chave de travamento.

#### Exemplo JSON

```json
{
  "telescopio_id": 1,
  "codigo": "Hubble-Acad",
  "nome": "Telescópio Espacial Acadêmico Hubble-Acad",
  "descricao": "Telescópio espacial compartilhado por instituições acadêmicas.",
  "status_operacional": "OPERACIONAL",
  "criado_em_utc": "2025-10-26T18:00:00Z",
  "_links": {
    "self": { "href": "/telescopios/1", "method": "GET" },
    "agendamentos": { "href": "/telescopios/1/agendamentos", "method": "GET" }
  }
}
```

---

### 2.3 Agendamento

Representa a reserva de uma janela de observação do telescópio.

| Campo | Tipo | Obrigatório | Descrição |
|---|---:|:---:|---|
| `agendamento_id` | inteiro | sim | Identificador único do agendamento. |
| `cientista_id` | inteiro | sim | Cientista responsável pela reserva. |
| `telescopio_id` | inteiro | sim | Telescópio reservado. |
| `horario_inicio_utc` | datetime UTC | sim | Início da janela de observação. |
| `horario_fim_utc` | datetime UTC | sim | Fim da janela de observação. |
| `timestamp_requisicao_utc` | datetime UTC | sim | Horário sincronizado usado no pedido do cliente. |
| `status` | texto | sim | Estado: `CONFIRMADO`, `CANCELADO` ou `REJEITADO`. |
| `objetivo_observacao` | texto | não | Descrição breve do objetivo científico. |
| `criado_em_utc` | datetime UTC | sim | Data e hora em que o registro foi criado. |
| `cancelado_em_utc` | datetime UTC | não | Data e hora de cancelamento, se houver. |

#### Regras iniciais

- Dois agendamentos confirmados não podem ocupar o mesmo telescópio no mesmo intervalo de tempo.
- A primeira versão do sistema considera a menor unidade de reserva como um slot de 5 minutos.
- O horário deve ser informado em UTC.
- Agendamentos cancelados permanecem registrados para auditoria.
- A criação de um agendamento confirmado deve gerar log de auditoria `AGENDAMENTO_CRIADO`.
- O cancelamento de um agendamento deve gerar log de auditoria `AGENDAMENTO_CANCELADO`.

#### Chave lógica de recurso para lock

A chave de recurso usada pelo serviço coordenador deve combinar o telescópio e o início do slot:

```text
{codigo_telescopio}_{horario_inicio_utc}
```

Exemplo:

```text
Hubble-Acad_2025-12-01T03:00:00Z
```

#### Exemplo JSON

```json
{
  "agendamento_id": 123,
  "cientista_id": 7,
  "telescopio_id": 1,
  "horario_inicio_utc": "2025-12-01T03:00:00Z",
  "horario_fim_utc": "2025-12-01T03:05:00Z",
  "timestamp_requisicao_utc": "2025-10-26T18:00:05.123Z",
  "status": "CONFIRMADO",
  "objetivo_observacao": "Observação de emissão de radiação em região interestelar.",
  "criado_em_utc": "2025-10-26T18:00:05.123Z",
  "cancelado_em_utc": null,
  "_links": {
    "self": { "href": "/agendamentos/123", "method": "GET" },
    "cancelar": { "href": "/agendamentos/123/cancelar", "method": "POST" },
    "cientista": { "href": "/cientistas/7", "method": "GET" },
    "telescopio": { "href": "/telescopios/1", "method": "GET" }
  }
}
```

---

### 2.4 Log de Auditoria

Representa um evento imutável relevante para o negócio.

| Campo | Tipo | Obrigatório | Descrição |
|---|---:|:---:|---|
| `audit_log_id` | inteiro | sim | Identificador interno do registro de auditoria, se persistido em banco. |
| `timestamp_utc` | datetime UTC | sim | Momento exato do evento. |
| `level` | texto | sim | Nível lógico do evento. Para auditoria, usar `AUDIT`. |
| `event_type` | texto | sim | Tipo do evento de negócio. |
| `service` | texto | sim | Serviço que gerou o evento. |
| `request_id` | texto | sim | Identificador único da requisição, útil para rastreamento. |
| `actor` | objeto | sim | Quem executou a ação. |
| `details` | objeto | sim | Dados específicos do evento. |

#### Tipos de evento previstos

| Evento | Descrição |
|---|---|
| `AGENDAMENTO_CRIADO` | Agendamento confirmado com sucesso. |
| `AGENDAMENTO_CANCELADO` | Agendamento cancelado. |
| `AGENDAMENTO_REJEITADO_CONFLITO` | Tentativa rejeitada por conflito de horário ou lock ocupado. |
| `LOCK_SOLICITADO` | Serviço de agendamento solicitou lock ao coordenador. |
| `LOCK_CONCEDIDO` | Coordenador concedeu o lock. |
| `LOCK_NEGADO` | Coordenador negou lock por recurso ocupado. |
| `LOCK_LIBERADO` | Lock foi liberado após operação crítica. |

#### Exemplo JSON

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

## 3. Relacionamentos

```text
Cientista 1 ---- N Agendamento
Telescópio 1 ---- N Agendamento
Agendamento 1 ---- N Log de Auditoria
```

- Um cientista pode possuir vários agendamentos.
- Um telescópio pode possuir vários agendamentos, desde que não haja sobreposição entre agendamentos confirmados.
- Cada ação crítica relacionada a agendamento deve produzir um ou mais registros de log.

---

## 4. Estados do agendamento

```text
SOLICITADO -> CONFIRMADO
SOLICITADO -> REJEITADO
CONFIRMADO -> CANCELADO
```

Na implementação inicial, o estado `SOLICITADO` pode ser transitório e não persistido. A API pode retornar diretamente `CONFIRMADO` quando o agendamento for salvo ou `REJEITADO` quando houver conflito.

---

## 5. Restrições de consistência

1. `cientista_id` deve referenciar um cientista existente e ativo.
2. `telescopio_id` deve referenciar um telescópio existente e operacional.
3. `horario_inicio_utc` deve ser menor que `horario_fim_utc`.
4. O sistema deve rejeitar agendamento em horário já ocupado.
5. O sistema deve manter histórico de cancelamentos, sem apagar registros.
6. Todas as datas e horas trafegadas pela API devem estar em UTC e no formato ISO 8601.
7. A API deve retornar links HATEOAS nas respostas principais para permitir navegação por recursos relacionados.

---

## 6. Escopo desta entrega

Esta entrega define os modelos e regras de negócio iniciais. A persistência real com Flask, SQLAlchemy e SQLite será implementada na Entrega 2. O serviço coordenador de lock será implementado na Entrega 3.
