# Proiect final: manualele și garanțiile electrocasnicelor

Programul ajută la găsirea informațiilor din manualele și condițiile de garanție
pentru 10 electrocasnice. Răspunsul este în română și arată documentul și pagina.

Am două programe principale:

- `indexare.py` citește fișierele TXT/PDF și le indexează în ChromaDB.
- `agent.py` primește întrebări în terminal și folosește unealta `rag_search`.

## Pregătire

Rulez comenzile din folderul `AI-Agentic-Application`:

```powershell
uv sync --locked --extra semantic-search
uv run --extra semantic-search python proiect_final/electrocasnice/descarca_documente.py
```

A doua comandă descarcă documentele dacă lipsesc. Există 10 manuale și 3 garanții
comune pe producător, în `proiect_final/electrocasnice/documente`.
[Catalogul](electrocasnice/README.md) arată modelele și sursele oficiale.

În `.env` completez `API_KEY` și `MODEL` pentru OpenRouter. Modelul trebuie să
accepte unelte. Merg și numele de la curs: `OPEN_ROUTER_API_KEY` și `OPEN_ROUTER_MODEL_NAME`.

### Alternativă: Google AI Studio

Pot folosi și Gemini prin aceeași bibliotecă `openai`.
Generez cheia mea în [Google AI Studio](https://aistudio.google.com/api-keys),
apoi modific doar aceste valori în `.env` din rădăcina repository-ului:

```dotenv
API_KEY=cheia_mea_google
MODEL=gemini-3.5-flash-lite
API_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```

Repornesc interfața după schimbarea configurației. Nu public cheia în GitHub.
Modelul are [nivel gratuit](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite),
cu limitele proiectului afișate în AI Studio. Pentru OpenRouter folosesc adresa
`https://openrouter.ai/api/v1` și o cheie OpenRouter.
O cheie validă poate primi o eroare și când se consumă cota gratuită; asta nu înseamnă că a expirat.

## Rulare

În primul terminal pornesc Chroma și îl las deschis:

```powershell
uv run --extra semantic-search chroma run --path proiect_final/chroma_data --port 8000
```

În al doilea terminal indexez, apoi pornesc agentul:

```powershell
uv run --extra semantic-search python -m proiect_final.indexare
uv run --extra semantic-search python -m proiect_final.agent
```

Aleg numărul aparatului din listă, apoi scriu întrebările. `quit` închide agentul.
Pentru alt aparat pornesc din nou agentul. Opresc serverul cu `Ctrl+C`.

## Interfața cu chat

Pot folosi și `interfata.py`, o pagină locală făcută cu Streamlit. Folosește
aceeași indexare și același agent ca programele din terminal.

Instalez și dependența pentru interfață:

```powershell
uv sync --locked --extra semantic-search --extra interfata
```

Las serverul Chroma pornit în primul terminal, ca mai sus. În al doilea rulez:

```powershell
uv run --extra semantic-search --extra interfata streamlit run proiect_final/interfata.py
```

Deschid **http://localhost:8501**. Dacă `uv` nu este în PATH, după instalare pot rula
`.\.venv\Scripts\python.exe -m streamlit run proiect_final/interfata.py`.

1. Aleg doar **Electrocasnicul**, scriu întrebarea și apăs **Întreabă**.
2. Pentru fișiere noi folosesc bara laterală: **Încarcă PDF sau TXT**, **Salvează**, apoi **Indexează**.
3. În **Fișiere** văd documentele existente și le pot descărca apăsând pe numele lor.

Interfața caută în toate documentele indexate, fără selectarea manuală a fișierelor.
Producătorul și modelul aparatului ales sunt transmise agentului pentru căutare și răspuns.
La schimbarea aparatului începe o conversație nouă. **Șterge chatul** golește conversația curentă.
TXT trebuie să fie UTF-8; limita este 50 MB pe fișier. Fișierele existente nu se suprascriu.
Încărcarea salvează local fișierele în același folder de documente, ignorat de Git.
Reindexarea reface toată colecția, inclusiv fișierele noi; nu pornește singură la încărcare.
Interfața se folosește local și nu cere cheia API în browser: o citește din `.env`.
Opresc ambele programe cu `Ctrl+C` în terminalele lor.

## Cum funcționează

Indexarea parcurge toate fișierele TXT/PDF din folderul documentelor.
Pentru manualele multilingve folosește secțiunile în română din catalog și
păstrează numărul original al paginii PDF. TXT este considerat pagina 1.
Manualul frigiderului este în engleză. Imaginile fără text nu sunt interpretate.

Textul este împărțit în fragmente de 800 de caractere, cu 120 comune.
Fiecare fragment are `source`, `page` și `chunk`.
Vectorii se calculează local cu `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
La prima rulare modelul se descarcă în `.model_cache`.
Folosesc `upsert`, în loturi de 100, în colecția `proiect_final_electrocasnice`.
La reindexare refac doar această colecție, ca să nu rămână duplicate sau surse vechi.

Agentul validează întrebarea cu Pydantic. Unealta validează separat argumentele
și caută hibrid, ca în lecția 8:

- Chroma caută după sens. Păstrez candidații semantici cu distanță cosinus de cel mult `0.5`.
- BM25 caută după cuvinte și coduri. Păstrez doar scorurile pozitive.
- Combin clasamentele: locul 1 primește 1 punct, locul 2 primește 1/2 etc.
- Aleg cele mai bune 10 fragmente, cu fișier, pagină și numărul fragmentului.

BM25 poate recupera un pasaj cu termeni exacți chiar dacă acel pasaj nu a trecut
pragul semantic. Indexul BM25 este refolosit cât timp textele nu se schimbă.
În interfață căutarea este în toată biblioteca. În terminal folosesc manualul
și garanția aparatului ales, prin filtrul de metadate `source`.

Contextul uneltei este text simplu, validat cu `RootModel[str]`.
LangGraph coordonează trei pași: `agent → cautare → raspuns`.
Starea este validată cu Pydantic, iar reducer-ul adaugă mesajele la conversație.
Textul găsit ajunge în mesajul `tool`, înaintea răspunsului final.
Dacă nu există rezultate relevante, graful se încheie cu un mesaj scurt,
fără al doilea apel LLM. Graful nu are bucle: face cel mult două apeluri LLM pe întrebare.
Fragmentele găsite sunt trimise furnizorului API configurat pentru acest răspuns.

## Legătura cu lecțiile

| Lecție / temă | Unde o folosesc |
|---|---|
| Python, clase, JSON, fișiere, șiruri | Catalog, citirea documentelor, tokenizarea pentru BM25 |
| Lecția 3: Pydantic | Întrebare, argumentele uneltei, context și starea grafului |
| Lecția 6: agent cu unelte | Schema `rag_search`, apelarea uneltei, mesajul `tool` și răspunsul LLM |
| Lecția 8: RAG și hybrid search | Chunking, embeddings, Chroma, BM25 și combinarea clasamentelor în `cautare.py` |
| Lecțiile 9–10: LangGraph | Noduri, stare, reducer și ramura fără rezultate în `agent.py` |
| Tema cu prag de distanță | Filtrarea candidaților din căutarea semantică |

Surse: [lecția 8](https://github.com/doublemacro/python-ai/blob/main/lesson_08_semantic_search.py),
[lecția 10](https://github.com/doublemacro/python-ai/blob/main/lesson_10_langgraph.py).
Reordonarea este făcută prin combinarea clasamentelor din curs. Tema opțională
cu `CrossEncoder` rămâne în `tema_3_optionala.py`; aici păstrez cele 10 fragmente
cerute de proiectul final și evit încărcarea unui model suplimentar.

Răspunsul trebuie să indice fișierul și pagina PDF. Dacă informația nu apare în
documente, agentului i se cere să spună asta. Condițiile generale nu confirmă
automat garanția unui aparat personal sau o extensie promoțională.
Formularea LLM-ului se verifică în documentul și pagina citate.
La verificarea manuală, modelul configurat a dat și un răspuns greșit despre
actele necesare pentru garanție, deși cita pagina. Citația singură nu confirmă
corectitudinea răspunsului; verific pasajul original.

## Exemple

- Aleg **2, mașina de spălat rufe**: `Ce documente sunt necesare pentru o solicitare de garantie?`
- Aleg **6, aparatul de cafea**: `Cum se curata unitatea de infuzare?`
- Aleg **7, blenderul**: `Pot folosi accesorii de la alt producator?`
- Încerc și: `Cat costa exact reparatia acestui aparat?` Dacă documentele nu dau un preț, agentul trebuie să spună că informația lipsește.

## Verificare scurtă

```powershell
uv run --extra semantic-search python -m pytest tests/test_proiect_final.py -q -p no:cacheprovider --basetemp=../.tools/pytest-final-electrocasnice
```

Sunt doar trei teste: indexarea și paginile; validarea, căutarea hibridă și pragul;
apoi fluxul grafului și trimiterea contextului în mesajele LLM. Folosesc un LLM simulat.

Dacă `uv` nu este în PATH, pot folosi `..\.tools\uv\uv.exe`.
După instalare, programele merg și cu `.\.venv\Scripts\python.exe`,
iar serverul cu `.\.venv\Scripts\chroma.exe`.
Documentele producătorilor, baza Chroma, modelele și `.env` rămân locale.
