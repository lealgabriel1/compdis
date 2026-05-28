import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sctec.db")
LOG_PATH = os.path.join(BASE_DIR, "app.log")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Atraso proposital para evidenciar a condição de corrida na Entrega 2.
# Várias requisições conseguem verificar "sem conflito" antes da primeira gravar.
RACE_DELAY_SECONDS = float(os.getenv("RACE_DELAY_SECONDS", "0.35"))

db = SQLAlchemy(app)


# ============================================================
# Models
# ============================================================

class Cientista(db.Model):
    __tablename__ = "cientistas"

    cientista_id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(160), nullable=False, unique=True)
    instituicao = db.Column(db.String(160), nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)


class Telescopio(db.Model):
    __tablename__ = "telescopios"

    telescopio_id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(80), nullable=False, unique=True)
    nome = db.Column(db.String(160), nullable=False)
    status_operacional = db.Column(db.String(40), nullable=False, default="OPERACIONAL")


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


# ============================================================
# Utils
# ============================================================

def utc_now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def gerar_request_id():
    return f"req-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"


def configurar_logs():
    logger_root = logging.getLogger()
    logger_root.setLevel(logging.INFO)
    logger_root.handlers.clear()

    formato = logging.Formatter(
        "%(levelname)s:%(asctime)sZ:%(name)s:%(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    arquivo = logging.FileHandler(LOG_PATH, encoding="utf-8")
    arquivo.setFormatter(formato)
    logger_root.addHandler(arquivo)

    console = logging.StreamHandler()
    console.setFormatter(formato)
    logger_root.addHandler(console)


configurar_logs()
logger = logging.getLogger("servico-agendamento")


def log_auditoria(event_type, request_id, actor, details):
    """
    Log de auditoria da Entrega 2.

    O enunciado permite usar WARNING ou um nível customizado AUDIT.
    Aqui usamos WARNING para aparecer claramente no app.log, mas o JSON
    interno carrega "level": "AUDIT".
    """
    evento = {
        "timestamp_utc": utc_now_iso(),
        "level": "AUDIT",
        "event_type": event_type,
        "service": "servico-agendamento",
        "request_id": request_id,
        "actor": actor,
        "details": details,
    }

    logger.warning(json.dumps(evento, ensure_ascii=False, sort_keys=True))


def erro(codigo, mensagem, http_status, request_id=None):
    return jsonify({
        "erro": {
            "codigo": codigo,
            "mensagem": mensagem,
            "request_id": request_id or gerar_request_id(),
        },
        "_links": {
            "agendamentos": {
                "href": "/agendamentos",
                "method": "GET",
            }
        },
    }), http_status


def popular_dados_iniciais():
    if not Cientista.query.get(1):
        db.session.add(Cientista(
            cientista_id=1,
            nome="Marie Curie",
            email="marie.curie@universidade-paris.fr",
            instituicao="Universidade de Paris",
            ativo=True,
        ))

    if not Telescopio.query.get(1):
        db.session.add(Telescopio(
            telescopio_id=1,
            codigo="Hubble-Acad",
            nome="Telescópio Espacial Acadêmico Hubble-Acad",
            status_operacional="OPERACIONAL",
        ))

    db.session.commit()


def existe_conflito(telescopio_id, inicio, fim):
    """
    Verificação simples de conflito de horário.

    Na Entrega 2 ela é propositalmente insuficiente sob concorrência:
    várias threads verificam antes de qualquer uma gravar, então todas
    acreditam que o horário está livre.
    """
    return Agendamento.query.filter(
        Agendamento.telescopio_id == telescopio_id,
        Agendamento.status == "CONFIRMADO",
        Agendamento.horario_inicio_utc < fim,
        Agendamento.horario_fim_utc > inicio,
    ).first() is not None


def agendamento_to_dict(agendamento):
    return {
        "agendamento_id": agendamento.agendamento_id,
        "cientista_id": agendamento.cientista_id,
        "telescopio_id": agendamento.telescopio_id,
        "horario_inicio_utc": agendamento.horario_inicio_utc,
        "horario_fim_utc": agendamento.horario_fim_utc,
        "timestamp_requisicao_utc": agendamento.timestamp_requisicao_utc,
        "status": agendamento.status,
        "objetivo_observacao": agendamento.objetivo_observacao,
        "criado_em_utc": agendamento.criado_em_utc,
        "_links": {
            "self": {
                "href": f"/agendamentos/{agendamento.agendamento_id}",
                "method": "GET",
            },
            "cientista": {
                "href": f"/cientistas/{agendamento.cientista_id}",
                "method": "GET",
            },
            "telescopio": {
                "href": f"/telescopios/{agendamento.telescopio_id}",
                "method": "GET",
            },
        },
    }


with app.app_context():
    db.create_all()
    popular_dados_iniciais()


# ============================================================
# Rotas auxiliares para demonstração
# ============================================================

@app.route("/")
def home():
    return jsonify({
        "mensagem": "SCTEC - Serviço de Agendamento - Entrega 2",
        "_links": {
            "agendamentos": {
                "href": "/agendamentos",
                "method": "GET",
            },
            "criar_agendamento": {
                "href": "/agendamentos",
                "method": "POST",
            },
            "reset_teste": {
                "href": "/debug/reset",
                "method": "POST",
            },
        },
    })


@app.route("/debug/reset", methods=["POST"])
def reset_debug():
    """
    Rota auxiliar para regravar o vídeo/teste da Entrega 2.

    Ela limpa os agendamentos e o app.log, permitindo executar o teste
    de estresse novamente a partir de uma base limpa.
    """
    Agendamento.query.delete()
    db.session.commit()

    open(LOG_PATH, "w", encoding="utf-8").close()
    logger.info("Base de agendamentos e app.log reiniciados para teste")

    return jsonify({
        "status": "resetado",
        "_links": {
            "agendamentos": {
                "href": "/agendamentos",
                "method": "GET",
            }
        },
    })


# ============================================================
# Rotas principais
# ============================================================

@app.route("/cientistas/<int:cientista_id>")
def obter_cientista(cientista_id):
    cientista = Cientista.query.get_or_404(cientista_id)

    return jsonify({
        "cientista_id": cientista.cientista_id,
        "nome": cientista.nome,
        "email": cientista.email,
        "instituicao": cientista.instituicao,
        "ativo": cientista.ativo,
        "_links": {
            "self": {
                "href": f"/cientistas/{cientista.cientista_id}",
                "method": "GET",
            },
            "agendamentos": {
                "href": f"/agendamentos?cientista_id={cientista.cientista_id}",
                "method": "GET",
            },
            "criar_agendamento": {
                "href": "/agendamentos",
                "method": "POST",
            },
        },
    })


@app.route("/telescopios/<int:telescopio_id>")
def obter_telescopio(telescopio_id):
    telescopio = Telescopio.query.get_or_404(telescopio_id)

    return jsonify({
        "telescopio_id": telescopio.telescopio_id,
        "codigo": telescopio.codigo,
        "nome": telescopio.nome,
        "status_operacional": telescopio.status_operacional,
        "_links": {
            "self": {
                "href": f"/telescopios/{telescopio.telescopio_id}",
                "method": "GET",
            },
            "agendamentos": {
                "href": f"/agendamentos?telescopio_id={telescopio.telescopio_id}",
                "method": "GET",
            },
        },
    })


@app.route("/agendamentos", methods=["GET", "POST"])
def agendamentos():
    if request.method == "GET":
        query = Agendamento.query

        cientista_id = request.args.get("cientista_id")
        telescopio_id = request.args.get("telescopio_id")

        if cientista_id:
            query = query.filter(Agendamento.cientista_id == int(cientista_id))
        if telescopio_id:
            query = query.filter(Agendamento.telescopio_id == int(telescopio_id))

        itens = query.order_by(Agendamento.agendamento_id).all()

        return jsonify({
            "items": [agendamento_to_dict(item) for item in itens],
            "_links": {
                "self": {
                    "href": "/agendamentos",
                    "method": "GET",
                },
                "criar": {
                    "href": "/agendamentos",
                    "method": "POST",
                },
            },
        })

    request_id = request.headers.get("X-Request-ID", gerar_request_id())
    data = request.get_json(silent=True) or {}

    logger.info("Requisição recebida para POST /agendamentos")

    campos_obrigatorios = ["cientista_id", "horario_inicio_utc"]
    for campo in campos_obrigatorios:
        if not data.get(campo):
            return erro("DADOS_INVALIDOS", f"Campo obrigatório ausente: {campo}", 400, request_id)

    cientista = Cientista.query.get(data["cientista_id"])
    if not cientista or not cientista.ativo:
        return erro("CIENTISTA_INVALIDO", "Cientista inexistente ou inativo.", 400, request_id)

    telescopio_id = int(data.get("telescopio_id", 1))
    telescopio = Telescopio.query.get(telescopio_id)
    if not telescopio or telescopio.status_operacional != "OPERACIONAL":
        return erro("TELESCOPIO_INDISPONIVEL", "Telescópio inexistente ou indisponível.", 400, request_id)

    inicio = data["horario_inicio_utc"]
    fim = data.get("horario_fim_utc", "2025-12-01T03:05:00Z")
    timestamp_requisicao = data.get("timestamp_requisicao_utc", utc_now_iso())

    logger.info("Iniciando verificação de conflito no BD")
    conflito = existe_conflito(telescopio.telescopio_id, inicio, fim)

    # Atraso intencional para demonstrar a condição de corrida.
    # Sem lock/coordenador, várias requisições concorrentes passam por aqui.
    time.sleep(RACE_DELAY_SECONDS)

    if conflito:
        logger.info("Conflito encontrado no BD")
        return erro("CONFLITO_DE_HORARIO", "Já existe agendamento confirmado para este intervalo.", 409, request_id)

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

    log_auditoria(
        "AGENDAMENTO_CRIADO",
        request_id,
        actor={
            "type": "CIENTISTA",
            "cientista_id": cientista.cientista_id,
            "nome": cientista.nome,
        },
        details={
            "agendamento_id": agendamento.agendamento_id,
            "cientista_id": cientista.cientista_id,
            "telescopio_id": telescopio.telescopio_id,
            "horario_inicio_utc": agendamento.horario_inicio_utc,
            "horario_fim_utc": agendamento.horario_fim_utc,
            "status": agendamento.status,
        },
    )

    return jsonify(agendamento_to_dict(agendamento)), 201


@app.route("/agendamentos/<int:agendamento_id>")
def obter_agendamento(agendamento_id):
    agendamento = Agendamento.query.get_or_404(agendamento_id)
    return jsonify(agendamento_to_dict(agendamento))


if __name__ == "__main__":
    porta = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=porta, threaded=True, debug=False)
