import argparse
import collections
import json
import threading
import time
from datetime import datetime, timezone

import requests

URL_AGENDAMENTO = "http://127.0.0.1:5000/agendamentos"
URL_RESET = "http://127.0.0.1:5000/debug/reset"
NUMERO_DE_REQUISICOES = 10

PAYLOAD_CONFLITANTE = {
    "cientista_id": 1,
    "telescopio_id": 1,
    "horario_inicio_utc": "2025-12-01T03:00:00Z",
    "horario_fim_utc": "2025-12-01T03:05:00Z",
    "objetivo_observacao": "Teste de concorrência do SCTEC.",
}

resultados = []
lock = threading.Lock()


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def resetar_base():
    try:
        response = requests.post(URL_RESET, timeout=5)
        print(f"Reset: {response.status_code} - {response.text[:120]}")
    except requests.RequestException as exc:
        print(f"Aviso: não foi possível resetar a base automaticamente: {exc}")


def fazer_requisicao_agendamento(thread_num):
    payload = dict(PAYLOAD_CONFLITANTE)
    payload["timestamp_requisicao_utc"] = utc_now_iso()
    print(f"[Thread {thread_num}]: Iniciando requisição...")

    try:
        response = requests.post(
            URL_AGENDAMENTO,
            json=payload,
            headers={"X-Request-ID": f"teste-thread-{thread_num}"},
            timeout=15,
        )
        resumo = {
            "thread": thread_num,
            "status_code": response.status_code,
            "body": response.text[:220],
        }
        with lock:
            resultados.append(resumo)
        print(f"[Thread {thread_num}]: Status {response.status_code} - {response.text[:120]}...")
    except requests.exceptions.ConnectionError as exc:
        print(f"[Thread {thread_num}]: Erro de conexão. O Flask está rodando? {exc}")
    except Exception as exc:
        print(f"[Thread {thread_num}]: Erro inesperado: {exc}")


def consultar_agendamentos():
    try:
        response = requests.get(URL_AGENDAMENTO, timeout=5)
        print("\nAgendamentos no banco:")
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    except Exception as exc:
        print(f"Não foi possível consultar /agendamentos: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Teste de estresse SCTEC")
    parser.add_argument("--no-reset", action="store_true", help="não limpa a base antes do teste")
    parser.add_argument("-n", "--numero", type=int, default=NUMERO_DE_REQUISICOES)
    args = parser.parse_args()

    if not args.no_reset:
        resetar_base()

    print(f"\nDisparando {args.numero} requisições simultâneas para {URL_AGENDAMENTO}")
    print(f"Payload base: {PAYLOAD_CONFLITANTE}\n")

    threads = []
    start_time = time.time()

    for i in range(args.numero):
        t = threading.Thread(target=fazer_requisicao_agendamento, args=(i + 1,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    end_time = time.time()
    contagem = collections.Counter(r["status_code"] for r in resultados)
    print(f"\nResumo HTTP: {dict(contagem)}")
    print(f"Tempo total: {end_time - start_time:.2f} segundos")
    consultar_agendamentos()
