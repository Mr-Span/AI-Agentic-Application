import json
import os
import sys
from pathlib import Path

PROIECT = Path(__file__).resolve().parents[1]
CATALOG = Path(__file__).with_name("electrocasnice") / "catalog.json"
SURSE = CATALOG.parent / "documente"
CACHE = PROIECT / ".model_cache"
COLECTIE = "proiect_final_electrocasnice"
MODEL_EMBEDDING = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MARIME_CHUNK = 800
SUPRAPUNERE = 120
MARIME_LOT = 100


def citeste_catalog():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def conecteaza():
    import chromadb
    from chromadb.config import Settings

    try:
        return chromadb.HttpClient(host="localhost", port=8000,
                                   settings=Settings(anonymized_telemetry=False))
    except Exception:
        raise ConnectionError("Nu pot ajunge la Chroma. Porneste serverul pe portul 8000.") from None


def incarca_model():
    os.environ.setdefault("HF_HOME", str(CACHE))
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_EMBEDDING, device="cpu", cache_folder=str(CACHE))


def imparte_text(text):
    bucati = []
    pas = MARIME_CHUNK - SUPRAPUNERE
    for start in range(0, len(text), pas):
        # Păstrăm puțin text comun între două fragmente vecine.
        bucata = text[start:start + MARIME_CHUNK].strip()
        if bucata:
            bucati.append(bucata)
        if start + MARIME_CHUNK >= len(text):
            break
    return bucati


def citeste_pagini(cale, document=None):
    document = document or {}
    if cale.suffix.lower() == ".pdf":
        import pymupdf

        with pymupdf.open(cale) as pdf:
            pagini = [(numar + 1, pagina.get_text()) for numar, pagina in enumerate(pdf)]
    else:
        # Un fișier TXT este tratat ca o singură pagină.
        pagini = [(1, cale.read_text(encoding="utf-8-sig"))]
    # Alegem româna fără să schimbăm numerele paginilor din PDF.
    if document.get("pagini_ro"):
        prima, ultima = document["pagini_ro"]
        pagini = [(numar, text) for numar, text in pagini if prima <= numar <= ultima]
    if document.get("inceput_text") and pagini:
        numar, text = pagini[0]
        pagini[0] = (numar, text[text.index(document["inceput_text"]):])
    if document.get("sfarsit_text") and pagini:
        numar, text = pagini[-1]
        pagini[-1] = (numar, text[:text.index(document["sfarsit_text"])])
    return pagini


def indexeaza(collection, model, folder=SURSE):
    if not folder.is_dir():
        raise ValueError("Lipsesc documentele. Ruleaza intai proiect_final/electrocasnice/descarca_documente.py.")
    documente = {d["fisier"]: d for d in citeste_catalog()["documente"]}
    # Ștergem indexul vechi, ca să nu rămână duplicate sau fișiere eliminate.
    vechi = collection.get(include=[])["ids"]
    for start in range(0, len(vechi), MARIME_LOT):
        collection.delete(ids=vechi[start:start + MARIME_LOT])

    total = 0
    for cale in sorted(folder.iterdir()):
        if not cale.is_file() or cale.suffix.lower() not in {".txt", ".pdf"}:
            continue
        try:
            pagini = citeste_pagini(cale, documente.get(cale.name))
        except (OSError, ValueError, RuntimeError):
            print(f"Nu pot citi {cale.name}. Verifica documentul.")
            continue
        texte = []
        ids = []
        metadate = []
        numar_chunk = 0
        for pagina, text in pagini:
            for bucata in imparte_text(text):
                numar_chunk += 1
                texte.append(bucata)
                ids.append(f"{cale.name}:{numar_chunk}")
                metadate.append({"source": cale.name, "page": pagina, "chunk": numar_chunk})
        if not texte:
            print(f"{cale.name}: nu contine text de indexat.")
            continue

        # Lucrăm pe loturi mici, inclusiv când calculăm vectorii.
        for start in range(0, len(texte), MARIME_LOT):
            final = start + MARIME_LOT
            lot = texte[start:final]
            vectori = model.encode(lot, normalize_embeddings=True).tolist()
            collection.upsert(
                ids=ids[start:final],
                documents=lot,
                metadatas=metadate[start:final],
                embeddings=vectori,
            )
        total += len(texte)
        print(f"{cale.name}: {len(texte)} fragmente incarcate")
    return total


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        client = conecteaza()
        collection = client.get_or_create_collection(
            COLECTIE, embedding_function=None, configuration={"hnsw": {"space": "cosine"}},
        )
        print("Incarc modelul de embeddings. Prima rulare poate dura mai mult.")
        model = incarca_model()
        total = indexeaza(collection, model)
    except (ConnectionError, ValueError) as eroare:
        raise SystemExit(str(eroare))
    print(f"Indexare terminata: {total} fragmente in colectia {COLECTIE}.")


if __name__ == "__main__":
    main()
