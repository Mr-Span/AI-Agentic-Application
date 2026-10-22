# Proiect final: căutare în documente cu RAG

Am două programe:

- `indexare.py` citește fișierele și le pune în ChromaDB.
- `agent.py` răspunde la întrebări folosind documentele indexate.

## Cum îl pornesc

Rulez comenzile din folderul `AI-Agentic-Application`.
Instalez bibliotecile o singură dată:

```powershell
uv sync --locked --extra semantic-search
```

În `.env` completez `API_KEY` și `MODEL` pentru OpenRouter.
Modelul trebuie să accepte unelte. Merg și numele de la curs:
`OPEN_ROUTER_API_KEY` și `OPEN_ROUTER_MODEL_NAME`.

În primul terminal pornesc baza de date și o las deschisă:

```powershell
uv run --extra semantic-search chroma run --path proiect_final/chroma_data --port 8000
```

În al doilea terminal indexez documentele, apoi pornesc agentul:

```powershell
uv run --extra semantic-search python -m proiect_final.indexare
uv run --extra semantic-search python -m proiect_final.agent
```

Scriu `quit` ca să ies din agent. Opresc serverul cu `Ctrl+C`.

## Ce se întâmplă în cod

În `data_sources` sunt `paragraphs.txt`, `invoices.pdf` și `StarMaker.pdf`.
Pot adăuga și alte fișiere TXT sau PDF. PDF-urile sunt citite pe pagini;
pentru TXT folosesc pagina 1. Un PDF scanat are nevoie de OCR separat.

Împart textul în fragmente de 800 de caractere, cu 120 de caractere comune.
Fiecare fragment are `source` (numele fișierului), `page` și `chunk`.
Numărul fragmentului începe de la 1 pentru fiecare document.

Calculez vectorii local cu `sentence-transformers/all-MiniLM-L6-v2` și îi pun
în colecția `proiect_final` prin `upsert`, în loturi de cel mult 100.
La reindexare refac această colecție, ca să elimin duplicatele și sursele vechi.

Agentul validează întrebarea cu Pydantic și cere unealta `rag_search`.
Unealta validează și argumentele primite de la model, caută cele mai apropiate
10 fragmente (sau câte există) și întoarce text simplu, validat cu `RootModel[str]`.
Textul conține sursa, pagina și numărul fragmentului.

Pun rezultatul în mesajul `tool`, apoi cer răspunsul final în română, cu surse
și pagini. Dacă documentele nu conțin răspunsul, modelului i se cere să spună asta.
La lipsa serverului, a indexului sau la o eroare API afișez un mesaj scurt.

## Întrebări de încercat

```text
What did Marcus do during the meeting?
What is the amount due for invoice INV-2026-1003 for Cedar Grove Clinic?
According to StarMaker.pdf, how does the narrator explore the universe?
quit
```

Documentele sunt în engleză, dar răspunsurile sunt cerute în română.
Factura din exemplu are valoarea `$2,175.00`, la pagina 3 din `invoices.pdf`.

## Dacă uv nu este în PATH pe Windows

Pentru instalare folosesc `..\.tools\uv\uv.exe sync --locked --extra semantic-search`.
După instalare, cele trei comenzi merg și cu executabilele locale:

```powershell
.\.venv\Scripts\chroma.exe run --path proiect_final/chroma_data --port 8000
.\.venv\Scripts\python.exe -m proiect_final.indexare
.\.venv\Scripts\python.exe -m proiect_final.agent
```

## Verificare scurtă

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_proiect_final.py -q -p no:cacheprovider --basetemp=../.tools/pytest-proiect-final
```

Sunt doar trei teste: indexarea și metadatele, validarea Pydantic, apoi trimiterea
contextului către model. Folosesc un model simulat și nu consumă credit API.
Baza `chroma_data`, modelele descărcate și `.env` rămân locale, ignorate de Git.
