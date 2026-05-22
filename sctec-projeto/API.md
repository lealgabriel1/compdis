# SCTEC - Entrega 1: Especificação da API RESTful

**Sistema:** Sistema de Controle de Telescópio Espacial Compartilhado (SCTEC)  
**Entrega:** 1 - Definições da API  
**Objetivo:** definir o contrato da API, os endpoints, os payloads, as respostas, os códigos HTTP e os links HATEOAS.

---

## 1. Convenções gerais

### 1.1 Base URL

```text
http://localhost:5000
```

### 1.2 Formato de dados

Todas as requisições e respostas usam JSON.

```http
Content-Type: application/json
Accept: application/json
```

### 1.3 Datas e horas

Todas as datas devem usar UTC no formato ISO 8601.

```text
2025-12-01T03:00:00Z
2025-10-26T18:00:05.123Z
```

### 1.4 Estrutura padrão de erro

```json
{
  "erro": {
    "codigo": "CONFLITO_AGENDAMENTO",
    "mensagem": "Já existe agendamento confirmado para este telescópio neste horário.",
    "request_id": "req-20251026-000124"
  },
  "_links": {
    "agendamentos": { "href": "/agendamentos", "method": "GET" }
  }
}
```

### 1.5 Códigos HTTP utilizados

| Código | Uso |
|---:|---|
| `200 OK` | Consulta bem-sucedida. |
| `201 Created` | Recurso criado com sucesso. |
| `400 Bad Request` | Payload inválido ou campos obrigatórios ausentes. |
| `404 Not Found` | Recurso inexistente. |
| `409 Conflict` | Conflito de agendamento ou lock ocupado. |
| `500 Internal Server Error` | Erro inesperado no serviço. |

---

## 2. Endpoints de Cientistas

### 2.1 Criar cientista

```http
POST /cientistas
```

#### Request

```json
{
  "nome": "Marie Curie",
  "email": "marie.curie@universidade-paris.fr",
  "instituicao": "Universidade de Paris",
  "pais": "França",
  "area_pesquisa": "Radiação cósmica"
}
```

#### Response - `201 Created`

```json
{
  "cientista_id": 7,
  "nome": "Marie Curie",
  "email": "marie.curie@universidade-paris.fr",
  "instituicao": "Universidade de Paris",
  "pais": "França",
  "area_pesquisa": "Radiação cósmica",
  "ativo": true,
  "criado_em_utc": "2025-10-26T18:00:00Z",
  "_links": {
    "self": { "href": "/cientistas/7", "method": "GET" },
    "agendamentos": { "href": "/cientistas/7/agendamentos", "method": "GET" },
    "criar_agendamento": { "href": "/agendamentos", "method": "POST" }
  }
}
```

---

### 2.2 Listar cientistas

```http
GET /cientistas
```

#### Response - `200 OK`

```json
{
  "items": [
    {
      "cientista_id": 7,
      "nome": "Marie Curie",
      "instituicao": "Universidade de Paris",
      "_links": {
        "self": { "href": "/cientistas/7", "method": "GET" },
        "agendamentos": { "href": "/cientistas/7/agendamentos", "method": "GET" }
      }
    }
  ],
  "_links": {
    "self": { "href": "/cientistas", "method": "GET" },
    "criar": { "href": "/cientistas", "method": "POST" }
  }
}
```

---

### 2.3 Consultar cientista por ID

```http
GET /cientistas/{cientista_id}
```

#### Response - `200 OK`

```json
{
  "cientista_id": 7,
  "nome": "Marie Curie",
  "email": "marie.curie@universidade-paris.fr",
  "instituicao": "Universidade de Paris",
  "pais": "França",
  "area_pesquisa": "Radiação cósmica",
  "ativo": true,
  "_links": {
    "self": { "href": "/cientistas/7", "method": "GET" },
    "agendamentos": { "href": "/cientistas/7/agendamentos", "method": "GET" },
    "criar_agendamento": { "href": "/agendamentos", "method": "POST" }
  }
}
```

---

### 2.4 Listar agendamentos de um cientista

```http
GET /cientistas/{cientista_id}/agendamentos
```

#### Response - `200 OK`

```json
{
  "cientista_id": 7,
  "items": [
    {
      "agendamento_id": 123,
      "horario_inicio_utc": "2025-12-01T03:00:00Z",
      "horario_fim_utc": "2025-12-01T03:05:00Z",
      "status": "CONFIRMADO",
      "_links": {
        "self": { "href": "/agendamentos/123", "method": "GET" },
        "cancelar": { "href": "/agendamentos/123/cancelar", "method": "POST" }
      }
    }
  ],
  "_links": {
    "cientista": { "href": "/cientistas/7", "method": "GET" },
    "criar_agendamento": { "href": "/agendamentos", "method": "POST" }
  }
}
```

---

## 3. Endpoints de Telescópios

### 3.1 Listar telescópios

```http
GET /telescopios
```

#### Response - `200 OK`

```json
{
  "items": [
    {
      "telescopio_id": 1,
      "codigo": "Hubble-Acad",
      "nome": "Telescópio Espacial Acadêmico Hubble-Acad",
      "status_operacional": "OPERACIONAL",
      "_links": {
        "self": { "href": "/telescopios/1", "method": "GET" },
        "agendamentos": { "href": "/telescopios/1/agendamentos", "method": "GET" }
      }
    }
  ],
  "_links": {
    "self": { "href": "/telescopios", "method": "GET" }
  }
}
```

---

### 3.2 Consultar telescópio por ID

```http
GET /telescopios/{telescopio_id}
```

#### Response - `200 OK`

```json
{
  "telescopio_id": 1,
  "codigo": "Hubble-Acad",
  "nome": "Telescópio Espacial Acadêmico Hubble-Acad",
  "descricao": "Telescópio espacial compartilhado por instituições acadêmicas.",
  "status_operacional": "OPERACIONAL",
  "_links": {
    "self": { "href": "/telescopios/1", "method": "GET" },
    "agendamentos": { "href": "/telescopios/1/agendamentos", "method": "GET" }
  }
}
```

---

### 3.3 Listar agendamentos de um telescópio

```http
GET /telescopios/{telescopio_id}/agendamentos
```

#### Query parameters opcionais

| Parâmetro | Exemplo | Descrição |
|---|---|---|
| `inicio_utc` | `2025-12-01T00:00:00Z` | Início do período de consulta. |
| `fim_utc` | `2025-12-02T00:00:00Z` | Fim do período de consulta. |

#### Response - `200 OK`

```json
{
  "telescopio_id": 1,
  "items": [
    {
      "agendamento_id": 123,
      "cientista_id": 7,
      "horario_inicio_utc": "2025-12-01T03:00:00Z",
      "horario_fim_utc": "2025-12-01T03:05:00Z",
      "status": "CONFIRMADO",
      "_links": {
        "self": { "href": "/agendamentos/123", "method": "GET" },
        "cientista": { "href": "/cientistas/7", "method": "GET" }
      }
    }
  ],
  "_links": {
    "telescopio": { "href": "/telescopios/1", "method": "GET" }
  }
}
```

---

## 4. Endpoints de Agendamentos

### 4.1 Criar agendamento

```http
POST /agendamentos
```

Este endpoint cria uma solicitação de reserva. Na Entrega 2, ele demonstrará a falha de concorrência. Na Entrega 3, ele será protegido pelo serviço coordenador de lock.

#### Request

```json
{
  "cientista_id": 7,
  "telescopio_id": 1,
  "horario_inicio_utc": "2025-12-01T03:00:00Z",
  "horario_fim_utc": "2025-12-01T03:05:00Z",
  "timestamp_requisicao_utc": "2025-10-26T18:00:05.123Z",
  "objetivo_observacao": "Observação de emissão de radiação em região interestelar."
}
```

#### Response - `201 Created`

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
  "_links": {
    "self": { "href": "/agendamentos/123", "method": "GET" },
    "cancelar": { "href": "/agendamentos/123/cancelar", "method": "POST" },
    "cientista": { "href": "/cientistas/7", "method": "GET" },
    "telescopio": { "href": "/telescopios/1", "method": "GET" }
  }
}
```

#### Response - `409 Conflict`

```json
{
  "erro": {
    "codigo": "RECURSO_OCUPADO",
    "mensagem": "O recurso Hubble-Acad_2025-12-01T03:00:00Z já está ocupado ou em processamento.",
    "request_id": "req-20251026-000124"
  },
  "_links": {
    "agendamentos": { "href": "/agendamentos", "method": "GET" },
    "telescopio": { "href": "/telescopios/1", "method": "GET" }
  }
}
```

---

### 4.2 Listar agendamentos

```http
GET /agendamentos
```

#### Query parameters opcionais

| Parâmetro | Exemplo | Descrição |
|---|---|---|
| `cientista_id` | `7` | Filtra por cientista. |
| `telescopio_id` | `1` | Filtra por telescópio. |
| `status` | `CONFIRMADO` | Filtra por status. |
| `inicio_utc` | `2025-12-01T00:00:00Z` | Início do período. |
| `fim_utc` | `2025-12-02T00:00:00Z` | Fim do período. |

#### Response - `200 OK`

```json
{
  "items": [
    {
      "agendamento_id": 123,
      "cientista_id": 7,
      "telescopio_id": 1,
      "horario_inicio_utc": "2025-12-01T03:00:00Z",
      "horario_fim_utc": "2025-12-01T03:05:00Z",
      "status": "CONFIRMADO",
      "_links": {
        "self": { "href": "/agendamentos/123", "method": "GET" },
        "cancelar": { "href": "/agendamentos/123/cancelar", "method": "POST" },
        "cientista": { "href": "/cientistas/7", "method": "GET" },
        "telescopio": { "href": "/telescopios/1", "method": "GET" }
      }
    }
  ],
  "_links": {
    "self": { "href": "/agendamentos", "method": "GET" },
    "criar": { "href": "/agendamentos", "method": "POST" }
  }
}
```

---

### 4.3 Consultar agendamento por ID

```http
GET /agendamentos/{agendamento_id}
```

#### Response - `200 OK`

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

### 4.4 Cancelar agendamento

```http
POST /agendamentos/{agendamento_id}/cancelar
```

#### Request

```json
{
  "motivo": "Cancelamento solicitado pelo cientista responsável."
}
```

#### Response - `200 OK`

```json
{
  "agendamento_id": 123,
  "status": "CANCELADO",
  "cancelado_em_utc": "2025-10-26T19:15:00Z",
  "motivo_cancelamento": "Cancelamento solicitado pelo cientista responsável.",
  "_links": {
    "self": { "href": "/agendamentos/123", "method": "GET" },
    "cientista": { "href": "/cientistas/7", "method": "GET" },
    "telescopio": { "href": "/telescopios/1", "method": "GET" }
  }
}
```

---

## 5. Endpoint de tempo oficial

### 5.1 Consultar tempo do servidor

```http
GET /time
```

Esse endpoint permite que o cliente sincronize seu relógio lógico com o servidor antes de enviar uma solicitação de agendamento.

#### Response - `200 OK`

```json
{
  "server_time_utc": "2025-10-26T18:00:05.123Z",
  "epoch_ms": 1761501605123,
  "_links": {
    "self": { "href": "/time", "method": "GET" },
    "criar_agendamento": { "href": "/agendamentos", "method": "POST" }
  }
}
```

---

## 6. Endpoints previstos do Serviço Coordenador

O serviço coordenador será implementado em Node.js/Express na Entrega 3. Ele não possui regra de negócio de telescópio; sua função é controlar locks por recurso.

### 6.1 Solicitar lock

```http
POST http://localhost:3000/lock
```

#### Request

```json
{
  "resource": "Hubble-Acad_2025-12-01T03:00:00Z",
  "request_id": "req-20251026-000123"
}
```

#### Response - `200 OK`

```json
{
  "status": "LOCK_GRANTED",
  "resource": "Hubble-Acad_2025-12-01T03:00:00Z",
  "_links": {
    "unlock": { "href": "/unlock", "method": "POST" }
  }
}
```

#### Response - `409 Conflict`

```json
{
  "status": "LOCK_DENIED",
  "resource": "Hubble-Acad_2025-12-01T03:00:00Z",
  "message": "Recurso já está em uso."
}
```

---

### 6.2 Liberar lock

```http
POST http://localhost:3000/unlock
```

#### Request

```json
{
  "resource": "Hubble-Acad_2025-12-01T03:00:00Z",
  "request_id": "req-20251026-000123"
}
```

#### Response - `200 OK`

```json
{
  "status": "LOCK_RELEASED",
  "resource": "Hubble-Acad_2025-12-01T03:00:00Z"
}
```

---

## 7. Mapeamento de logs por endpoint

| Endpoint | Log de aplicação | Log de auditoria |
|---|---|---|
| `GET /time` | Requisição recebida para sincronização de tempo. | Não obrigatório. |
| `POST /agendamentos` | Requisição recebida, tentativa de lock, verificação de conflito, persistência. | `AGENDAMENTO_CRIADO` ou `AGENDAMENTO_REJEITADO_CONFLITO`. |
| `POST /agendamentos/{id}/cancelar` | Requisição de cancelamento recebida. | `AGENDAMENTO_CANCELADO`. |
| `POST /lock` | Pedido de lock recebido, concedido ou negado. | Opcional no coordenador; log operacional é suficiente nesta etapa. |
| `POST /unlock` | Pedido de unlock recebido e lock liberado. | Opcional no coordenador; log operacional é suficiente nesta etapa. |

---

## 8. Observação sobre HATEOAS

As respostas principais incluem `_links` para que o cliente descubra as próximas ações possíveis a partir do próprio recurso retornado. Por exemplo, um agendamento confirmado inclui link de cancelamento, enquanto um agendamento cancelado não deve oferecer novamente a ação `cancelar`.
