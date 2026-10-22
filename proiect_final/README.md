# Proiect final: RAG cu ChromaDB

Doua programe Python, rulate separat din terminal:

- [indexare.py](indexare.py) citeste documentele si le incarca in baza de date.
- [agent.py](agent.py) raspunde folosind unealta `rag_search` si documentele deja indexate.

## Pregatire

Toate comenzile se ruleaza din folderul **AI-Agentic-Application**, unde este
`pyproject.toml`, nu din subfolderul `proiect_final`.

```powershell
uv sync --locked --extra semantic-search
```

In `.env` din radacina repository-ului completezi `API_KEY` cu cheia OpenRouter
si `MODEL` cu un model care accepta apelarea uneltelor. Sunt acceptate si
numele de la curs: `OPEN_ROUTER_API_KEY` si `OPEN_ROUTER_MODEL_NAME`.
Daca exista ambele variante, `API_KEY` si `MODEL` au prioritate.

Modelul de embeddings este `sentence-transformers/all-MiniLM-L6-v2` si ruleaza
local, pe CPU. La prima folosire se descarca in `.model_cache/`.
Cheia se foloseste doar de agent, pentru cererile OpenRouter.

## 1. Pornesc serverul Chroma

In primul terminal:

```powershell
uv run --extra semantic-search chroma run --path proiect_final/chroma_data --port 8000
```

Las acest terminal deschis. Cele doua programe se conecteaza prin
`chromadb.HttpClient(host="localhost", port=8000)`.

Datele bazei raman in `proiect_final/chroma_data/`, ignorat de Git.
La repornirea serverului folosesc aceeasi comanda si aceeasi cale.

## 2. Indexez documentele

In al doilea terminal:

```powershell
uv run --extra semantic-search python -m proiect_final.indexare
```

Folderul [data_sources](data_sources) contine trei exemple de la curs:

| Document | Continut |
| --- | --- |
| `paragraphs.txt` | Activitatile lui Marcus la o intalnire |
| `invoices.pdf` | Patru facturi fictive |
| `StarMaker.pdf` | Textul despre Star Maker folosit la curs |

Pot adauga alte fisiere `.txt` sau `.pdf` direct in acest folder.
Programul citeste textul PDF pe pagini cu PyMuPDF. Pentru TXT considera
continutul ca fiind pagina 1. Un PDF scanat fara text necesita OCR separat.

Textul fiecarei pagini este impartit in bucati de maximum 800 de caractere,
cu 120 de caractere comune intre doua bucati. Fiecare fragment are metadatele:

```python
{"source": "invoices.pdf", "page": 3, "chunk": 3}
```

`chunk` incepe de la 1 si continua pe toate paginile acelui document.
Vectorii sunt normalizati si incarcati cu `collection.upsert`, pe loturi.
Colectia `proiect_final` foloseste distanta cosinus.

La o noua rulare refacem continutul acestei colectii. Astfel nu apar duplicate
si nu raman fragmente din documentele eliminate. Fisierele goale, tipurile
nesuportate si documentele care nu pot fi citite nu sunt indexate.
Programul afiseaza numarul de fragmente si se inchide.

## 3. Pornesc agentul

Dupa terminarea indexarii, in acelasi al doilea terminal:

```powershell
uv run --extra semantic-search python -m proiect_final.agent
```

Intrebarea este validata cu Pydantic: trebuie sa fie text si sa nu fie goala.
Agentul cere unealta `rag_search` cu argumentul `question`.
Validam din nou argumentele uneltei, apoi cautam cele mai apropiate 10 fragmente
din intreaga colectie. Daca baza are mai putine, folosim cate sunt disponibile.

Contextul include textul, fisierul, pagina si numarul fiecarui fragment.
Este validat cu `RootModel[str]` si returnat ca string simplu.
Il adaugam in mesajele conversatiei cu `role="tool"` si `tool_call_id`,
apoi cerem modelului raspunsul final. Unealta face cautarea local; agentul
este cel care comunica cu OpenRouter.

Raspunsul trebuie sa fie in romana si sa citeze sursa, de exemplu
`[invoices.pdf, pagina 3]`. Daca fragmentele nu contin raspunsul, modelului
i se cere sa spuna asta, fara sa inventeze informatii.

Intrebari de demonstratie, una pentru fiecare document:

```text
What did Marcus do during the meeting?
What is the amount due for invoice INV-2026-1003 for Cedar Grove Clinic?
According to StarMaker.pdf, how does the narrator explore the universe?
quit
```

Documentele de exemplu sunt in engleza, asa ca intrebarile de verificare sunt
tot in engleza. Raspunsurile agentului sunt cerute in romana.
Pentru factura `INV-2026-1003`, verific pagina 3: suma este `$2,175.00`.
Pentru Marcus, sursa este `paragraphs.txt`, pagina 1.

## Comenzi locale pe Windows

Daca `uv` nu este in PATH, instalarea se poate face cu:

```powershell
..\.tools\uv\uv.exe sync --locked --extra semantic-search
```

Dupa instalare, aceleasi trei etape pot fi rulate direct:

```powershell
# Primul terminal:
.\.venv\Scripts\chroma.exe run --path proiect_final/chroma_data --port 8000

# Al doilea terminal:
.\.venv\Scripts\python.exe -m proiect_final.indexare
.\.venv\Scripts\python.exe -m proiect_final.agent
```

Pentru oprire scriu `quit` la agent si apas `Ctrl+C` in terminalul serverului.

## Verificari minime

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_proiect_final.py -q
```

Sunt trei teste: metadatele si reindexarea fara duplicate, validarea Pydantic
pentru intrebare si context, apoi fluxul unealta-raspuns cu un LLM simulat.
Testele nu consuma credit OpenRouter.

Verificat local pe 22 octombrie 2026: serverul HTTP a primit cele trei
documente, iar doua rulari ale indexarii au pastrat **133 de fragmente**, fara
duplicate. Cele trei intrebari de demonstratie au fost adresate si modelului
OpenRouter configurat. Agentul a raspuns in romana, cu citatii: Marcus din
`paragraphs.txt`, factura de `$2,175.00` din `invoices.pdf`, pagina 3, si
calatoria naratorului din `StarMaker.pdf`. Cele trei teste automate trec.

Daca serverul nu este pornit sau colectia nu este indexata, programul afiseaza
ce pas trebuie rulat. Erorile OpenRouter sunt afisate prin tipul lor, fara cheie.
Modelul configurat trebuie sa accepte `tools` si `tool_choice`.

Referinte: [Chroma client-server](https://docs.trychroma.com/docs/run-chroma/client-server),
[function calling din documentatia OpenAI](https://developers.openai.com/api/docs/guides/function-calling)
si [RootModel din Pydantic](https://docs.pydantic.dev/latest/concepts/models/#rootmodel-and-custom-root-types).
