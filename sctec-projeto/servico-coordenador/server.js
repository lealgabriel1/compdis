const express = require('express');

const app = express();
const port = process.env.PORT || 3000;
const locks = new Map();

app.use(express.json());

function now() {
  return new Date().toISOString();
}

function log(message) {
  console.log(`${now()}:servico-coordenador:${message}`);
}

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', locks_ativos: locks.size });
});

app.post('/lock', (req, res) => {
  const { resource, request_id } = req.body || {};

  if (!resource) {
    return res.status(400).json({
      erro: { codigo: 'DADOS_INVALIDOS', mensagem: 'Campo obrigatório ausente: resource', request_id },
    });
  }

  log(`Recebido pedido de lock para o recurso ${resource}`);

  if (locks.has(resource)) {
    log(`Recurso ${resource} já está em uso, negando lock`);
    return res.status(409).json({
      status: 'NEGADO',
      resource,
      locked_by: locks.get(resource).request_id,
      request_id,
    });
  }

  locks.set(resource, { request_id, acquired_at: now() });
  log(`Lock concedido para o recurso ${resource}`);
  return res.status(200).json({ status: 'CONCEDIDO', resource, request_id });
});

app.post('/unlock', (req, res) => {
  const { resource, request_id } = req.body || {};

  if (!resource) {
    return res.status(400).json({
      erro: { codigo: 'DADOS_INVALIDOS', mensagem: 'Campo obrigatório ausente: resource', request_id },
    });
  }

  if (locks.has(resource)) {
    locks.delete(resource);
    log(`Recebido pedido de unlock para o recurso ${resource}. Lock liberado`);
    return res.status(200).json({ status: 'LIBERADO', resource, request_id });
  }

  log(`Recebido pedido de unlock para o recurso ${resource}, mas nenhum lock estava ativo`);
  return res.status(200).json({ status: 'NAO_EXISTIA', resource, request_id });
});

app.listen(port, '0.0.0.0', () => {
  log(`Servidor iniciado na porta ${port}`);
});
