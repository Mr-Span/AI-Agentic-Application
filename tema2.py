import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

PROIECT = Path(__file__).resolve().parent


def fisiere_proiect():
    # Excludem fisierele locale care nu fac parte din tema.
    for folder, directoare, fisiere in PROIECT.walk():
        directoare[:] = [d for d in directoare if d not in
                        {".git", ".venv", "__pycache__", ".pytest_cache"}]
        for nume in sorted(fisiere):
            cale = folder / nume
            if not nume.startswith(".env") and not cale.is_symlink():
                yield cale


def listeaza_fisiere():
    return "\n".join(sorted(p.relative_to(PROIECT).as_posix() for p in fisiere_proiect()))


def cauta_cuvant():
    gasite = []
    for cale in fisiere_proiect():
        try:
            text = cale.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # Sarim peste fisierele care nu sunt text UTF-8.
        if "pytest" in text.lower():
            gasite.append(cale.relative_to(PROIECT).as_posix())
    return "\n".join(sorted(gasite)) or "Nu am gasit fisiere."


def ruleaza_agent(client, model):
    unelte = {"listeaza_fisiere": listeaza_fisiere, "cauta_cuvant": cauta_cuvant}
    tools = [
        {"type": "function", "function": {
            "name": nume,
            "description": descriere,
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        }}
        for nume, descriere in [
            ("listeaza_fisiere", "Listeaza fisierele proiectului."),
            ("cauta_cuvant", "Cauta pytest in continutul fisierelor."),
        ]
    ]
    mesaje = [{"role": "user", "content":
               "Listeaza fisierele, apoi cauta pytest. Enumera toate fisierele gasite."}]

    # LLM-ul apeleaza intai listarea, apoi cautarea.
    for nume in unelte:
        raspuns = client.chat.completions.create(
            model=model, messages=mesaje, tools=tools,
            tool_choice={"type": "function", "function": {"name": nume}},
            parallel_tool_calls=False,
        ).choices[0].message
        apeluri = raspuns.tool_calls or []
        if len(apeluri) != 1 or apeluri[0].function.name != nume:
            raise ValueError(f"Modelul trebuie sa apeleze {nume}.")
        apel = apeluri[0]
        if json.loads(apel.function.arguments) != {}:
            raise ValueError("Uneltele nu primesc argumente.")
        rezultat = unelte[nume]()
        mesaje.append(raspuns.model_dump(exclude_none=True))
        mesaje.append({"role": "tool", "tool_call_id": apel.id, "content": rezultat})

    return client.chat.completions.create(
        model=model, messages=mesaje, tools=tools, tool_choice="none",
    ).choices[0].message.content


if __name__ == "__main__":
    load_dotenv(PROIECT / ".env")
    cheie = os.getenv("API_KEY")
    if not cheie:
        raise SystemExit("Completeaza API_KEY in fisierul .env.")
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=cheie, timeout=60)
    print(ruleaza_agent(client, os.getenv("MODEL", "minimax/minimax-m3")))
