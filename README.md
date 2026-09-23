# AI Agentic Application

Teme pentru curs, in Python. Proiect initializat cu uv, teste cu pytest.

## Tema 1

In `tema_1.py` citesc datele din `student.json` cu `json.load`, apoi le
validez cu Pydantic: numele este text, varsta este un intreg pozitiv,
iar emailul trebuie sa aiba un format valid.

`Student` este un alt nume pentru `StudentValidator`, fiindca in enunt apar ambele.
`Student(**date)` transmite campurile din dictionar catre clasa pentru validare.

## Rulare

Ai nevoie de [uv](https://docs.astral.sh/uv/getting-started/installation/).
Din folderul proiectului:

```bash
uv sync --locked
uv run python tema_1.py
uv run python -m pytest
```

Exemplul din tema afiseaza:

```text
Ana Popescu, 20 ani, ana.popescu@example.com
```

## Alte exemple

In `exemple/` sunt inca trei studenti: Mihai (22 ani), Elena (19 ani)
si Andrei (24 ani). Poti alege fisierul la rulare:

```bash
uv run python tema_1.py exemple/mihai.json
uv run python tema_1.py exemple/elena.json
uv run python tema_1.py exemple/andrei.json
```

Testele verifica cele patru fisiere si resping un email gresit sau o varsta
de 0 ori -1. Poti incerca si tu aceste valori intr-un JSON: Pydantic va ridica
`ValidationError`. Adresele de email sunt fictive.
