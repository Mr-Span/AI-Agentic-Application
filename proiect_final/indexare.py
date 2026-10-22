import os
import sys
from pathlib import Path

PROIECT = Path(__file__).resolve().parents[1]
SURSE = Path(__file__).with_name("data_sources")
CACHE = PROIECT / ".model_cache"
COLECTIE = "proiect_final"
MODEL_EMBEDDING = "sentence-transformers/all-MiniLM-L6-v2"


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
    for start in range(0, len(text), 680):
        # Înaintăm cu 680, ca să păstrăm 120 de caractere comune.
        bucata = text[start:start + 800].strip()
        if bucata:
            bucati.append(bucata)
        if start + 800 >= len(text):
            break
    return bucati


def citeste_pagini(cale):
    if cale.suffix.lower() == ".pdf":
        import pymupdf

        with pymupdf.open(cale) as document:
            return [(numar + 1, pagina.get_text()) for numar, pagina in enumerate(document)]
    # Un fișier TXT este tratat ca o singură pagină.
    return [(1, cale.read_text(encoding="utf-8-sig"))]


def indexeaza(collection, model, folder=SURSE):
    if not folder.is_dir():
        raise ValueError("Lipseste folderul proiect_final/data_sources.")
    # Refacem doar colecția proiectului final, inclusiv după ștergerea unui document.
    vechi = collection.get(include=[])["ids"]
    for start in range(0, len(vechi), 100):
        collection.delete(ids=vechi[start:start + 100])

    total = 0
    for cale in sorted(folder.iterdir()):
        if not cale.is_file() or cale.suffix.lower() not in {".txt", ".pdf"}:
            continue
        try:
            pagini = citeste_pagini(cale)
        except (OSError, ValueError, RuntimeError):
            print(f"Nu pot citi {cale.name}. Verifica documentul.")
            continue
        texte, ids, metadate = [], [], []
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

        vectori = model.encode(texte, normalize_embeddings=True).tolist()
        # Inserăm pe loturi mici, ca să putem procesa și PDF-uri mai lungi.
        for start in range(0, len(texte), 100):
            collection.upsert(
                ids=ids[start:start + 100], documents=texte[start:start + 100],
                metadatas=metadate[start:start + 100], embeddings=vectori[start:start + 100],
            )
        total += len(texte)
        print(f"{cale.name}: {len(texte)} fragmente incarcate")
    return total


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        client = conecteaza()
    except ConnectionError as eroare:
        raise SystemExit(str(eroare))
    collection = client.get_or_create_collection(
        COLECTIE, embedding_function=None, configuration={"hnsw": {"space": "cosine"}},
    )
    print("Incarc modelul de embeddings. Prima rulare poate dura mai mult.")
    model = incarca_model()
    try:
        total = indexeaza(collection, model)
    except ValueError as eroare:
        raise SystemExit(str(eroare))
    print(f"Indexare terminata: {total} fragmente in colectia {COLECTIE}.")


if __name__ == "__main__":
    main()
