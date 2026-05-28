import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sctec.db")
LOG_PATH = os.path.join(BASE_DIR, "app.log")

app = Flask(__name__, static_folder="static")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Para a Entrega 2: false => demonstra a condição de corrida.
# Para a Entrega 3/5: true => protege a seção crítica via serviço coordenador.
USE_COORDINATOR = os.getenv("USE_COORDINATOR", "false").lower() == "true"
COORDINATOR_URL = os.getenv("COORDINATOR_URL", "http://127.0.0.1:3000")
RACE_DELAY_SECONDS = float(os.getenv("RACE_DELAY_SECONDS", "0.35"))

db = SQLAlchemy(app)


class Cientista(db.Model):
    __tablename__ = "cientistas"

    cientista_id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(160), nullable=False, unique=True)
    instituicao = db.Column(db.String(160), nullable=False)
    pais = db.Column(db.String(80))
    area_pesquisa = db.Column(db.String(120))
    criado_em_utc = db.Column(db.String(40), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)


class Telescopio(db.Model):
    __tablename__ = "telescopios"

    telescopio_id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(80), nullable=False, unique=True)
    nome = db.Column(db.String(160), nullable=False)
    descricao = db.Column(db.Text)
    status_operacional = db.Column(db.String(40), nullable=False, default="OPERACIONAL")
    criado_em_utc = db.Column(db.String(40), nullable=False)


class Agendamento(db.Model):
    __tablename__ = "agendamentos"

    agendamento_id = db.Column(db.Integer, primary_key=True)
    cientista_id = db.Column(db.Integer, db.ForeignKey("cientistas.cientista_id"), nullable=False)
    telescopio_id = db.Column(db.Integer, db.ForeignKey("telescopios.telescopio_id"), nullable=False)
    horario_inicio_utc = db.Column(db.String(40), nullable=False)
    horario_fim_utc = db.Column(db.String(40), nullable=False)
    timestamp_requisicao_utc = db.Column(db.String(40), nullable=False)
    status = db.Column(db.String(40), nullable=False, default="CONFIRMADO")
    objetivo_observacao = db.Column(db.Text)
    criado_em_utc = db.Column(db.String(40), nullable=False)
    cancelado_em_utc = db.Column(db.String(40))
    motivo_cancelamento = db.Column(db.Text)


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def request_id():
    return f"req-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"


def configure_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(levelname)s:%(asctime)sZ:%(name)s:%(message)s", datefmt="%Y-%m-%dT%H:%M:%S")

    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


configure_logging()
logger = logging.getLogger("servico-agendamento")


def audit(event_type, req_id, actor, details):
    event = {
        "timestamp_utc": utc_now_iso(),
        "level": "AUDIT",
        "event_type": event_type,
        "service": "servico-agendamento",
        "request_id": req_id,
        "actor": actor,
        "details": details,
    }
    logger.warning(json.dumps(event, ensure_ascii=False, sort_keys=True))


def seed_data():
    if not Cientista.query.get(1):
        db.session.add(Cientista(
            cientista_id=1,
            nome="Marie Curie",
            email="marie.curie@universidade-paris.fr",
            instituicao="Universidade de Paris",
            pais="França",
            area_pesquisa="Radiação cósmica",
            criado_em_utc=utc_now_iso(),
            ativo=True,
        ))
    if not Cientista.query.get(2):
        db.session.add(Cientista(
            cientista_id=2,
            nome="Cecilia Payne-Gaposchkin",
            email="cecilia.payne@harvard.edu",
            instituicao="Harvard College Observatory",
            pais="Estados Unidos",
            area_pesquisa="Astrofísica estelar",
            criado_em_utc=utc_now_iso(),
            ativo=True,
        ))
    if not Telescopio.query.get(1):
        db.session.add(Telescopio(
            telescopio_id=1,
            codigo="Hubble-Acad",
            nome="Telescópio Espacial Acadêmico Hubble-Acad",
            descricao="Telescópio espacial compartilhado por instituições acadêmicas.",
            status_operacional="OPERACIONAL",
            criado_em_utc=utc_now_iso(),
        ))
    db.session.commit()


with app.app_context():
    db.create_all()
    seed_data()


def cientista_to_dict(cientista):
    return {
        "cientista_id": cientista.cientista_id,
        "nome": cientista.nome,
        "email": cientista.email,
        "instituicao": cientista.instituicao,
        "pais": cientista.pais,
        "area_pesquisa": cientista.area_pesquisa,
        "criado_em_utc": cientista.criado_em_utc,
        "ativo": cientista.ativo,
        "_links": {
            "self": {"href": f"/cientistas/{cientista.cientista_id}", "method": "GET"},
            "agendamentos": {"href": f"/cientistas/{cientista.cientista_id}/agendamentos", "method": "GET"},
            "criar_agendamento": {"href": "/agendamentos", "method": "POST"},
        },
    }


def telescopio_to_dict(telescopio):
    return {
        "telescopio_id": telescopio.telescopio_id,
        "codigo": telescopio.codigo,
        "nome": telescopio.nome,
        "descricao": telescopio.descricao,
        "status_operacional": telescopio.status_operacional,
        "criado_em_utc": telescopio.criado_em_utc,
        "_links": {
            "self": {"href": f"/telescopios/{telescopio.telescopio_id}", "method": "GET"},
            "agendamentos": {"href": f"/telescopios/{telescopio.telescopio_id}/agendamentos", "method": "GET"},
        },
    }


def agendamento_to_dict(agendamento, include_all=True):
    data = {
        "agendamento_id": agendamento.agendamento_id,
        "cientista_id": agendamento.cientista_id,
        "telescopio_id": agendamento.telescopio_id,
        "horario_inicio_utc": agendamento.horario_inicio_utc,
        "horario_fim_utc": agendamento.horario_fim_utc,
        "status": agendamento.status,
        "_links": {
            "self": {"href": f"/agendamentos/{agendamento.agendamento_id}", "method": "GET"},
            "cientista": {"href": f"/cientistas/{agendamento.cientista_id}", "method": "GET"},
            "telescopio": {"href": f"/telescopios/{agendamento.telescopio_id}", "method": "GET"},
        },
    }
    if agendamento.status == "CONFIRMADO":
        data["_links"]["cancelar"] = {"href": f"/agendamentos/{agendamento.agendamento_id}/cancelar", "method": "POST"}
    if include_all:
        data.update({
            "timestamp_requisicao_utc": agendamento.timestamp_requisicao_utc,
            "objetivo_observacao": agendamento.objetivo_observacao,
            "criado_em_utc": agendamento.criado_em_utc,
            "cancelado_em_utc": agendamento.cancelado_em_utc,
            "motivo_cancelamento": agendamento.motivo_cancelamento,
        })
    return data


def erro(codigo, mensagem, status_code, req_id=None, extra_links=None):
    payload = {
        "erro": {
            "codigo": codigo,
            "mensagem": mensagem,
            "request_id": req_id or request_id(),
        },
        "_links": extra_links or {"self": {"href": request.path, "method": request.method}},
    }
    return jsonify(payload), status_code


def has_conflict(telescopio_id, inicio, fim):
    return Agendamento.query.filter(
        Agendamento.telescopio_id == telescopio_id,
        Agendamento.status == "CONFIRMADO",
        Agendamento.horario_inicio_utc < fim,
        Agendamento.horario_fim_utc > inicio,
    ).first() is not None


def recurso_lock(telescopio, inicio):
    return f"{telescopio.codigo}_{inicio}"


def acquire_lock(recurso, req_id):
    logger.info("Tentando adquirir lock para o recurso %s", recurso)
    try:
        response = requests.post(f"{COORDINATOR_URL}/lock", json={"resource": recurso, "request_id": req_id}, timeout=3)
    except requests.RequestException as exc:
        logger.error("Erro ao comunicar com coordenador: %s", exc)
        return False, "COORDENADOR_INDISPONIVEL"

    if response.status_code == 200:
        logger.info("Lock adquirido com sucesso para o recurso %s", recurso)
        return True, None
    logger.info("Falha ao adquirir lock para o recurso %s, recurso ocupado", recurso)
    return False, "RECURSO_OCUPADO"


def release_lock(recurso, req_id):
    logger.info("Liberando lock para o recurso %s", recurso)
    try:
        requests.post(f"{COORDINATOR_URL}/unlock", json={"resource": recurso, "request_id": req_id}, timeout=3)
    except requests.RequestException as exc:
        logger.error("Erro ao liberar lock no coordenador: %s", exc)


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/time")
def server_time():
    logger.info("Requisição recebida em GET /time")
    now = datetime.now(timezone.utc)
    return jsonify({
        "server_time_utc": now.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "epoch_ms": int(now.timestamp() * 1000),
        "_links": {
            "self": {"href": "/time", "method": "GET"},
            "criar_agendamento": {"href": "/agendamentos", "method": "POST"},
        },
    })


@app.route("/cientistas", methods=["GET", "POST"])
def cientistas():
    if request.method == "GET":
        return jsonify({
            "items": [cientista_to_dict(c) for c in Cientista.query.order_by(Cientista.cientista_id).all()],
            "_links": {"self": {"href": "/cientistas", "method": "GET"}, "criar": {"href": "/cientistas", "method": "POST"}},
        })

    data = request.get_json(silent=True) or {}
    for field in ["nome", "email", "instituicao"]:
        if not data.get(field):
            return erro("DADOS_INVALIDOS", f"Campo obrigatório ausente: {field}", 400)
    cientista = Cientista(
        nome=data["nome"],
        email=data["email"],
        instituicao=data["instituicao"],
        pais=data.get("pais"),
        area_pesquisa=data.get("area_pesquisa"),
        criado_em_utc=utc_now_iso(),
        ativo=data.get("ativo", True),
    )
    db.session.add(cientista)
    db.session.commit()
    return jsonify(cientista_to_dict(cientista)), 201


@app.route("/cientistas/<int:cientista_id>")
def get_cientista(cientista_id):
    cientista = Cientista.query.get_or_404(cientista_id)
    return jsonify(cientista_to_dict(cientista))


@app.route("/cientistas/<int:cientista_id>/agendamentos")
def get_agendamentos_cientista(cientista_id):
    Cientista.query.get_or_404(cientista_id)
    itens = Agendamento.query.filter_by(cientista_id=cientista_id).order_by(Agendamento.agendamento_id).all()
    return jsonify({
        "items": [agendamento_to_dict(a, include_all=False) for a in itens],
        "_links": {
            "cientista": {"href": f"/cientistas/{cientista_id}", "method": "GET"},
            "criar_agendamento": {"href": "/agendamentos", "method": "POST"},
        },
    })


@app.route("/telescopios")
def telescopios():
    return jsonify({
        "items": [telescopio_to_dict(t) for t in Telescopio.query.order_by(Telescopio.telescopio_id).all()],
        "_links": {"self": {"href": "/telescopios", "method": "GET"}},
    })


@app.route("/telescopios/<int:telescopio_id>")
def get_telescopio(telescopio_id):
    telescopio = Telescopio.query.get_or_404(telescopio_id)
    return jsonify(telescopio_to_dict(telescopio))


@app.route("/telescopios/<int:telescopio_id>/agendamentos")
def get_agendamentos_telescopio(telescopio_id):
    Telescopio.query.get_or_404(telescopio_id)
    query = Agendamento.query.filter_by(telescopio_id=telescopio_id)
    if request.args.get("status"):
        query = query.filter_by(status=request.args["status"])
    itens = query.order_by(Agendamento.agendamento_id).all()
    return jsonify({
        "items": [agendamento_to_dict(a, include_all=False) for a in itens],
        "_links": {"telescopio": {"href": f"/telescopios/{telescopio_id}", "method": "GET"}},
    })


@app.route("/agendamentos", methods=["GET", "POST"])
def agendamentos():
    if request.method == "GET":
        query = Agendamento.query
        for field in ["cientista_id", "telescopio_id", "status"]:
            value = request.args.get(field)
            if value:
                query = query.filter(getattr(Agendamento, field) == value)
        itens = query.order_by(Agendamento.agendamento_id).all()
        return jsonify({
            "items": [agendamento_to_dict(a, include_all=False) for a in itens],
            "_links": {"self": {"href": "/agendamentos", "method": "GET"}, "criar": {"href": "/agendamentos", "method": "POST"}},
        })

    data = request.get_json(silent=True) or {}
    req_id = request.headers.get("X-Request-ID", request_id())
    logger.info("Requisição recebida para POST /agendamentos")

    required = ["cientista_id", "horario_inicio_utc"]
    for field in required:
        if not data.get(field):
            return erro("DADOS_INVALIDOS", f"Campo obrigatório ausente: {field}", 400, req_id)

    cientista = Cientista.query.get(data["cientista_id"])
    if not cientista or not cientista.ativo:
        return erro("CIENTISTA_INVALIDO", "Cientista inexistente ou inativo.", 400, req_id)

    telescopio_id = int(data.get("telescopio_id", 1))
    telescopio = Telescopio.query.get(telescopio_id)
    if not telescopio or telescopio.status_operacional != "OPERACIONAL":
        return erro("TELESCOPIO_INDISPONIVEL", "Telescópio inexistente ou indisponível.", 400, req_id)

    inicio = data["horario_inicio_utc"]
    fim = data.get("horario_fim_utc") or inicio.replace("03:00:00Z", "03:05:00Z")
    timestamp_requisicao = data.get("timestamp_requisicao_utc") or utc_now_iso()
    recurso = recurso_lock(telescopio, inicio)
    lock_obtido = False

    actor = {"type": "CIENTISTA", "cientista_id": cientista.cientista_id, "nome": cientista.nome}

    try:
        if USE_COORDINATOR:
            lock_obtido, lock_error = acquire_lock(recurso, req_id)
            if not lock_obtido:
                audit("AGENDAMENTO_REJEITADO_CONFLITO", req_id, actor, {
                    "cientista_id": cientista.cientista_id,
                    "telescopio_id": telescopio.telescopio_id,
                    "recurso_lock": recurso,
                    "motivo": lock_error,
                    "status": "REJEITADO",
                })
                return erro("RECURSO_OCUPADO", f"O recurso {recurso} já está ocupado ou em processamento.", 409, req_id, {
                    "agendamentos": {"href": "/agendamentos", "method": "GET"},
                    "telescopio": {"href": f"/telescopios/{telescopio.telescopio_id}", "method": "GET"},
                })

        logger.info("Iniciando verificação de conflito no BD")
        conflito = has_conflict(telescopio.telescopio_id, inicio, fim)

        # Atraso proposital: na Entrega 2, sem coordenador, várias threads passam
        # pela verificação antes que a primeira grave no banco, demonstrando a falha.
        time.sleep(RACE_DELAY_SECONDS)

        if conflito:
            audit("AGENDAMENTO_REJEITADO_CONFLITO", req_id, actor, {
                "cientista_id": cientista.cientista_id,
                "telescopio_id": telescopio.telescopio_id,
                "recurso_lock": recurso,
                "horario_inicio_utc": inicio,
                "horario_fim_utc": fim,
                "status": "REJEITADO",
            })
            return erro("CONFLITO_DE_HORARIO", "Já existe agendamento confirmado para este intervalo.", 409, req_id)

        logger.info("Salvando novo agendamento no BD")
        agendamento = Agendamento(
            cientista_id=cientista.cientista_id,
            telescopio_id=telescopio.telescopio_id,
            horario_inicio_utc=inicio,
            horario_fim_utc=fim,
            timestamp_requisicao_utc=timestamp_requisicao,
            status="CONFIRMADO",
            objetivo_observacao=data.get("objetivo_observacao", "Observação acadêmica do telescópio espacial."),
            criado_em_utc=utc_now_iso(),
        )
        db.session.add(agendamento)
        db.session.commit()

        audit("AGENDAMENTO_CRIADO", req_id, actor, {
            "agendamento_id": agendamento.agendamento_id,
            "cientista_id": cientista.cientista_id,
            "telescopio_id": telescopio.telescopio_id,
            "recurso_lock": recurso,
            "horario_inicio_utc": inicio,
            "horario_fim_utc": fim,
            "status": "CONFIRMADO",
        })
        return jsonify(agendamento_to_dict(agendamento)), 201
    finally:
        if USE_COORDINATOR and lock_obtido:
            release_lock(recurso, req_id)


@app.route("/agendamentos/<int:agendamento_id>")
def get_agendamento(agendamento_id):
    agendamento = Agendamento.query.get_or_404(agendamento_id)
    return jsonify(agendamento_to_dict(agendamento))


@app.route("/agendamentos/<int:agendamento_id>/cancelar", methods=["POST"])
def cancelar_agendamento(agendamento_id):
    req_id = request.headers.get("X-Request-ID", request_id())
    logger.info("Requisição recebida para POST /agendamentos/%s/cancelar", agendamento_id)
    agendamento = Agendamento.query.get_or_404(agendamento_id)
    data = request.get_json(silent=True) or {}

    if agendamento.status == "CANCELADO":
        return jsonify(agendamento_to_dict(agendamento)), 200

    agendamento.status = "CANCELADO"
    agendamento.cancelado_em_utc = utc_now_iso()
    agendamento.motivo_cancelamento = data.get("motivo", "Cancelamento solicitado pelo cliente.")
    db.session.commit()

    cientista = Cientista.query.get(agendamento.cientista_id)
    telescopio = Telescopio.query.get(agendamento.telescopio_id)
    audit("AGENDAMENTO_CANCELADO", req_id, {
        "type": "CIENTISTA",
        "cientista_id": agendamento.cientista_id,
        "nome": cientista.nome if cientista else None,
    }, {
        "agendamento_id": agendamento.agendamento_id,
        "cientista_id": agendamento.cientista_id,
        "telescopio_id": agendamento.telescopio_id,
        "recurso_lock": recurso_lock(telescopio, agendamento.horario_inicio_utc) if telescopio else None,
        "horario_inicio_utc": agendamento.horario_inicio_utc,
        "horario_fim_utc": agendamento.horario_fim_utc,
        "status": "CANCELADO",
        "motivo_cancelamento": agendamento.motivo_cancelamento,
    })
    return jsonify(agendamento_to_dict(agendamento)), 200


@app.route("/debug/reset", methods=["POST"])
def reset_debug():
    # Rota auxiliar para gravação do vídeo/testes. Não faz parte da API de produção.
    Agendamento.query.delete()
    db.session.commit()
    open(LOG_PATH, "w", encoding="utf-8").close()
    logger.info("Base de agendamentos e app.log reiniciados para teste")
    return jsonify({"status": "resetado", "_links": {"agendamentos": {"href": "/agendamentos", "method": "GET"}}})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, threaded=True, debug=False)
