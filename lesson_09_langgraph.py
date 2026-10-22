import argparse
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

PROJECT_ROOT = Path(__file__).resolve().parent
INCIDENT_API = "https://jsonplaceholder.typicode.com/todos/"


class State(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Starea este caietul comun în care nodurile pun rezultatele.
    log_file: str = "log_report.txt"
    errors: list[str] = Field(default_factory=list)
    response: str = ""
    simulate_api: bool = True


def read_log_report(state):
    path = (PROJECT_ROOT / state.log_file).resolve()
    path.relative_to(PROJECT_ROOT)
    if path.suffix.lower() != ".txt" or any(part.startswith(".") for part in path.relative_to(PROJECT_ROOT).parts):
        raise ValueError("Alege un raport .txt din proiect.")
    lines = path.read_text(encoding="utf-8").splitlines()
    errors = []
    for line in lines:
        # Căutăm nivelul ERROR de după dată și oră, nu un cuvânt din mesaj.
        fields = line.split(maxsplit=3)
        if len(fields) >= 3 and fields[2] == "ERROR":
            errors.append(line)
    print(f"citire> {path.name}: {len(errors)} erori")
    # Întoarcem doar câmpul schimbat; LangGraph păstrează restul stării.
    return {"errors": errors}


def check_for_errors(state):
    if state.errors:
        return "call_incident_api"
    return "report_all_ok"


def call_incident_api(state):
    count = len(state.errors)
    if state.simulate_api:
        print(f"incident> simulez trimiterea a {count} erori")
        return {"response": f"Simulare: incident pentru {count} erori."}

    import requests

    # Acesta este un API public de demonstrație; nu păstrează un incident real.
    payload = {"userId": 1, "title": f"Raport de curs: {count} erori", "completed": False}
    try:
        response = requests.post(INCIDENT_API, json=payload, timeout=15)
        response.raise_for_status()
        return {"response": f"API demo: HTTP {response.status_code}, {count} erori raportate."}
    except requests.RequestException:
        return {"response": "API-ul demo nu a raspuns corect. Incearca varianta simulata."}


def report_all_ok(state):
    print("rezultat> nu sunt erori in log")
    return {"response": "Nu sunt erori in log."}


def build_graph():
    from langgraph.graph import END, START, StateGraph

    builder = StateGraph(State)
    builder.add_node("read_log_report", read_log_report)
    builder.add_node("call_incident_api", call_incident_api)
    builder.add_node("report_all_ok", report_all_ok)
    builder.add_edge(START, "read_log_report")
    # După citire alegem o singură ramură, în funcție de erorile găsite.
    builder.add_conditional_edges("read_log_report", check_for_errors, {
        "call_incident_api": "call_incident_api",
        "report_all_ok": "report_all_ok",
    })
    builder.add_edge("call_incident_api", END)
    builder.add_edge("report_all_ok", END)
    return builder.compile()


def main():
    parser = argparse.ArgumentParser(description="Lectia 9: analiza logurilor cu LangGraph.")
    parser.add_argument("--log", default="log_report.txt", help="Raportul de citit din proiect.")
    parser.add_argument("--api", action="store_true", help="Foloseste API-ul demo in loc de simulare.")
    args = parser.parse_args()
    try:
        graph = build_graph()
        result = graph.invoke(State(log_file=args.log, simulate_api=not args.api))
    except ImportError:
        raise SystemExit("Instaleaza bibliotecile: uv sync --locked --extra langgraph")
    except (OSError, ValueError):
        raise SystemExit("Nu pot citi raportul. Alege un fisier .txt din proiect.")
    print("Erori gasite:", len(result["errors"]))
    print("Raspuns:", result["response"])


if __name__ == "__main__":
    main()
