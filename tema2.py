import json
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

PROIECT = Path(__file__).resolve().parent


class Listare(BaseModel, extra="forbid"):
    pass  # Listarea nu are nevoie de argumente.


class Cautare(BaseModel, extra="forbid"):
    cuvant: Literal["pytest"] = "pytest"


def fisiere_proiect():
    # Sarim peste Git, mediul virtual, cache si fisierele cu chei API.
    for folder, directoare, fisiere in PROIECT.walk():
        directoare[:] = [d for d in directoare if d not in
                        {".git", ".venv", "__pycache__", ".pytest_cache"}]
        for nume in sorted(fisiere):
            cale = folder / nume
            if not nume.startswith(".env") and not cale.is_symlink():
                yield cale


def listeaza_fisiere(args: dict) -> str:
    Listare.model_validate(args)
    return "\n".join(sorted(p.relative_to(PROIECT).as_posix() for p in fisiere_proiect()))


def cauta_cuvant(args: dict) -> str:
    date = Cautare.model_validate(args)
    gasite = []
    for cale in fisiere_proiect():
        try:
            text = cale.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # Cautam in fisiere text, nu in imagini sau alte binare.
        if date.cuvant.casefold() in text.casefold():
            gasite.append(cale.relative_to(PROIECT).as_posix())
    return "\n".join(sorted(gasite)) or "Nu am gasit fisiere."


def ruleaza_agent(client, model: str) -> str:
    unelte = {"listeaza_fisiere": listeaza_fisiere, "cauta_cuvant": cauta_cuvant}
    tools = [
        {"type": "function", "function": {
            "name": "listeaza_fisiere", "description": "Listeaza fisierele proiectului.",
            "parameters": Listare.model_json_schema(),
        }},
        {"type": "function", "function": {
            "name": "cauta_cuvant", "description": "Cauta pytest in continutul fisierelor.",
            "parameters": Cautare.model_json_schema(),
        }},
    ]
    mesaje = [
        {"role": "system", "content": "Foloseste uneltele. Raspunde in romana si enumera "
         "toate fisierele gasite, fara sa inventezi rezultate."},
        {"role": "user", "content": "Listeaza fisierele, apoi cauta pytest in proiect."},
    ]

    # Cerem modelului cele doua apeluri in ordinea ceruta de tema.
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
        rezultat = unelte[nume](json.loads(apel.function.arguments))
        mesaje.append(raspuns.model_dump(exclude_none=True))
        mesaje.append({"role": "tool", "tool_call_id": apel.id, "content": rezultat})

    # Modelul primeste rezultatele uneltelor si formuleaza raspunsul final.
    raspuns = client.chat.completions.create(
        model=model, messages=mesaje, tools=tools, tool_choice="none",
    ).choices[0].message
    if not raspuns.content:
        raise ValueError("Modelul nu a returnat un raspuns text.")
    return raspuns.content


if __name__ == "__main__":
    load_dotenv(PROIECT / ".env")
    cheie = os.getenv("API_KEY")
    if not cheie:
        raise SystemExit("Adauga API_KEY in .env, dupa modelul din .env.example.")
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=cheie, timeout=60)
    model = os.getenv("MODEL", "minimax/minimax-m3")
    print(ruleaza_agent(client, model))
