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
si mici. Sunt excluse `.git`, `.venv`, cache-urile Python/pytest, `chroma_db`,
`.model_cache` si fisierele `.env`.
Fisierele care nu pot fi citite ca text UTF-8 sunt sarite.

Copiaza `.env.example` in `.env` si completeaza `API_KEY` cu cheia ta OpenRouter.
`MODEL=cohere/north-mini-code:free` foloseste Cohere North Mini Code gratuit, cu suport pentru unelte.
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

## Lectiile recuperate

Exemple adaptate dupa [repository-ul profesorului](https://github.com/doublemacro/python-ai/tree/0fc43bc4329646bf9d3e87a5e837ebef23a2e3b3),
versiunea `0fc43bc`, verificata pe 8 octombrie 2026. Am pastrat numele
fisierelor de la curs si am explicat pasii in comentarii in romana.

| Fisier | Ce exersez |
| --- | --- |
| `01_fundamentals.py` | Variabile, liste, dictionare, functii, if, for, while si input |
| `lesson_02_classes_objects.py` | Clasa User, obiecte, metode, set si JSON |
| `lesson_03_data_validation.py` | Pydantic, limite pentru campuri, adresa si tratarea erorilor |
| `lesson_04_types.py` | type, isinstance si adnotari de tip |
| `lesson_05_json_data.py` | Citirea si validarea datelor din user_data.json |
| `lesson_06_simplest_agent.py` | Agent cu unelte pentru teste, rezumate si numarat cuvinte |
| `lesson_07_string_manipulation.py` | Indexare, lower, split, join, count si citirea unui text |
| `lesson_08_semantic_search.py` | Citirea unui PDF, embeddings, cautare semantica si raspuns cu surse |
| `99_temp.py` | Afisarea liniilor care contin un cuvant intreg |
| `workshop_cuvinte.py` | Rezolvarea exercitiului din t.txt |
| `main_target.py` | Varianta agentului care are doar unealta pentru teste |
| `main.py` | Exemplul initial cu o functie de salut |

`user_data.json`, `paragraphs.txt`, `t.txt`, `StarMaker.pdf`, `pytest.ini` si testele
de validare sunt preluate din repository-ul profesorului. Pentru lectia 8
am adaugat separat bibliotecile necesare, prin extra `semantic-search`.

Parcurg lectiile in ordinea numerelor. Fiecare se ruleaza separat, de exemplu:

```bash
uv run python 01_fundamentals.py
uv run python lesson_05_json_data.py
uv run python lesson_07_string_manipulation.py
uv run python workshop_cuvinte.py
uv run python -m pytest
```

In prima lectie scriu `q` ca sa ies din bucla de citire.
Exercitiul workshop trebuie sa afiseze 8 aparitii pentru `marcus` si 51 de
cuvinte in total. Cautarea ignora majusculele si semnele de punctuatie;
`marcus123` nu este acelasi cuvant ca `marcus`.

## Agentul din lectia 6

Foloseste `API_KEY` si `MODEL` din acelasi `.env` ca tema 2. Accepta si
`OPEN_ROUTER_API_KEY` / `OPEN_ROUTER_MODEL_NAME`, numele de la profesor.
Daca sunt prezente ambele variante, `API_KEY` si `MODEL` au prioritate.

```bash
uv run python lesson_06_simplest_agent.py
```

Exemple de mesaje:

- `Ruleaza testele din tests/test_validations.py.`
- `Numara cuvintele marcus si notebook din paragraphs.txt.`
- `Fa un rezumat pentru paragraphs.txt.`
- `quit` pentru iesire.

Modelul cere o unealta, Python executa functia si trimite rezultatul inapoi,
iar modelul formuleaza raspunsul final. Fluxul urmeaza exemplul de
[function calling din documentatia OpenAI](https://developers.openai.com/api/docs/guides/function-calling).
Pentru rezumate, modelul ales pe OpenRouter trebuie sa accepte si raspunsuri
structurate cu `json_schema`. Disponibilitatea modelului depinde de furnizor.

Spre deosebire de tema 2, rezumarea trimite continutul fisierului ales la
OpenRouter. Citirea exclude fisierele ascunse (inclusiv `.env`), iesirea din
proiect si fisierele de peste 100 KB. Numaram cuvintele local, iar testele
ruleaza cu acelasi Python ca agentul, inclusiv pe Windows.

`tests/test_lectii.py` verifica numararea, restrictiile de citire, rularea unui
test real si fluxul uneltelor cu raspunsuri simulate. Testele nu consuma API.
Apelurile reale catre OpenRouter nu au fost verificate in aceasta completare.

## Ultima lectie: 8, cautare semantica in PDF

Pornim de la PDF-ul `StarMaker.pdf`, exact ca la curs. Citim textul paginilor,
il impartim in bucati, transformam bucatile in liste de numere (embeddings),
apoi le salvam in Chroma. Transformam si intrebarea in numere si cautam
bucatile cu sens apropiat. La final, putem cere modelului un raspuns folosind
doar acele fragmente. Acest ultim pas se numeste RAG.

Modelul de embeddings ruleaza local; OpenRouter este folosit pentru formularea
raspunsului. Sunt doua modele cu roluri diferite. Pentru prima incercare
folosim `--fara-llm`, ca sa vedem cautarea separat.

Din folderul `AI-Agentic-Application`, in terminalul PowerShell:

```powershell
uv sync --locked --extra semantic-search
uv run --extra semantic-search python lesson_08_semantic_search.py --fara-llm
```

Daca `uv` nu este recunoscut in terminal, in acest workspace exista deja
executabilul local. Aceleasi comenzi se pot rula asa:

```powershell
..\.tools\uv\uv.exe sync --locked --extra semantic-search
..\.tools\uv\uv.exe run --extra semantic-search python lesson_08_semantic_search.py --fara-llm
```

Prima rulare descarca modelul de embeddings si poate dura mai mult.
Programul afiseaza numarul de bucati indexate, apoi asteapta la `tu>`.
Scrie cate o intrebare, de exemplu:

```text
What does the narrator see when looking at the stars?
How does the narrator travel through the universe?
Who is the Star Maker?
quit
```

PDF-ul este in engleza, asa ca incepem cu intrebari in engleza pentru acest
model. Fiecare fragment afisat are sursa si numarul paginii din PDF.
Deschide pagina indicata si compara textul: o cautare semantica gaseste
fragmente apropiate ca sens, dar nu garanteaza ca fiecare contine raspunsul.

Pentru raspunsuri in romana, folosind `API_KEY` si `MODEL` din `.env`:

```powershell
uv run --extra semantic-search python lesson_08_semantic_search.py
```

Aceasta varianta trimite intrebarea si fragmentele gasite la OpenRouter.
Programul afiseaza si fragmentele, ca sa poti verifica raspunsul si citatiile.
`quit` opreste ambele variante. Baza `chroma_db/` si modelul `.model_cache/`
raman locale si nu se trimit pe GitHub.

Bibliotecile folosite: [Chroma](https://docs.trychroma.com/reference/python/collection),
[PyMuPDF4LLM](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/api.html)
si [Sentence Transformers](https://sbert.net/docs/package_reference/sentence_transformer/model.html).

## Exercitii pentru lectia 8

Fa-le in ordine si noteaza ce ai observat. Nu trebuie sa rescrii tot programul.

1. **Intelege bucatile de text.** Ruleaza comanda de mai jos. Ar trebui sa
   vezi `[800, 800, 240]`: pasul este 680, iar ultimele 120 de caractere dintr-o
   bucata sunt repetate la inceputul urmatoarei.

   ```powershell
   uv run python -c "from lesson_08_semantic_search import chunk_text; print([len(x) for x in chunk_text('a' * 1600)])"
   ```

2. **Compara doua formulari.** In varianta `--fara-llm`, intreaba
   `How does the narrator travel through the universe?`, apoi
   `How does the storyteller explore the cosmos?`. Noteaza paginile gasite.
   Cate sunt comune? De ce poate gasi texte chiar daca nu folosesti aceleasi cuvinte?

3. **Schimba marimea bucatilor.** In `lesson_08_semantic_search.py`, pune
   `CHUNK_SIZE = 400` si `CHUNK_OVERLAP = 60`, apoi reporneste programul.
   Noteaza numarul nou de bucati si compara fragmentele pentru aceeasi intrebare.
   La final revino la 800 si 120.

4. **Citeste scorurile.** Rezultatul cautarii contine si `result['distances'][0]`.
   Adauga temporar `print(result['distances'][0])` dupa cautare, in `main`.
   Compara primele distante cu fragmentele. O distanta cosinus mai mica
   inseamna ca vectorii sunt mai apropiati; nu este un procent de adevar.

5. **Verifica un raspuns.** Porneste varianta cu OpenRouter si intreaba
   `Who is the Star Maker?`. Verifica fiecare pagina citata in PDF.
   Apoi intreaba `What is the current price of Bitcoin?`: raspunsul nu trebuie
   inventat din cunostintele modelului, deoarece fragmentele cartii nu au aceasta informatie.

Pentru recapitularea lectiei 7, ruleaza `uv run python workshop_cuvinte.py`:
trebuie sa obtii 8 aparitii pentru `marcus` si 51 de cuvinte in total.

Testele lectiei 8 ruleaza si fara descarcarea modelului sau cheie API:

```powershell
uv run python -m pytest tests/test_semantic_search.py -q
uv run python -m pytest -q
```

Verificare locala pe 8 octombrie 2026: toate cele 26 de teste trec. PDF-ul
profesorului are 21 de pagini, indexate in 132 de fragmente cu setarile initiale.
Am verificat si cautarea cu modelul real, filtrarea dupa PDF si reindexarea
fara duplicate. Raspunsurile OpenRouter sunt verificate prin simulari in teste.
