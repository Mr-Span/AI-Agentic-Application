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

Testul citeste `student.json` si verifica datele Anei. Celelalte fisiere sunt
exemple pe care le poti rula separat. Adresele de email sunt fictive.

## Tema 2

`tema2.py` foloseste OpenAI + OpenRouter, ca in exemplul de la curs.
Agentul apeleaza mai intai `listeaza_fisiere`, apoi `cauta_cuvant` pentru `pytest`
si afiseaza fisierele gasite. `tool_choice` fixeaza ordinea celor doua apeluri.

Uneltele folosesc Python pentru listare si cautare, ca sa mearga si pe Windows,
si pe Linux. Cautarea include subfolderele si ignora diferenta intre litere mari
si mici. Sunt excluse `.git`, `.venv`, cache-urile Python/pytest si fisierele `.env`.
Fisierele care nu pot fi citite ca text UTF-8 sunt sarite.

Copiaza `.env.example` in `.env` si completeaza `API_KEY` cu cheia ta OpenRouter.
`MODEL` are valoarea din curs; o poti schimba cu un model care accepta unelte.
Cheia se creeaza in [OpenRouter](https://openrouter.ai/settings/keys).
OpenRouter este un serviciu online, accesat prin biblioteca `openai`.
Cheia ramane locala, nu se publica pe GitHub.

```bash
uv sync --locked
uv run python tema2.py
uv run python -m pytest tests/test_tema2.py
```

Printre rezultate trebuie sa apara `pyproject.toml` si `tests/test_tema2.py`.
Testul ruleaza unealta reala de cautare si verifica daca rezultatul contine
`pyproject.toml`, asa cum permite cerinta. Nu foloseste simulari si nu testeaza
raspunsul LLM-ului. Pentru rularea agentului ai nevoie de cheia OpenRouter.

Referinta: [apelarea uneltelor](https://developers.openai.com/api/docs/guides/function-calling).

Protectii: cheia sta in `.env`, ignorat de Git si de unelte. Agentul poate doar
lista si cauta in proiect, fara comenzi de shell sau modificari de fisiere.
Nu urmareste legaturi catre alte foldere. Trimite modelului numai nume de fisiere,
nu continutul lor. Sunt cel mult 3 cereri, cu timeout de 60 secunde fiecare,
maximum 1024 tokenuri de raspuns per cerere si fara reincercari automate.
