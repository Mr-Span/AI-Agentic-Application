import re
from functools import lru_cache

from rank_bm25 import BM25Okapi

NUMAR_REZULTATE = 10
DISTANTA_MAXIMA = 0.5


def tokenize(text):
    return re.findall(r"\b\w+\b", text.lower())


@lru_cache(maxsize=2)
def index_bm25(documente):
    # Refolosim indexul cât timp textele sunt aceleași.
    return BM25Okapi([tokenize(text) for text in documente])


def cauta(collection, model, intrebare, surse=None):
    filtru = {"source": {"$in": surse}} if surse else None
    corpus = collection.get(where=filtru, include=["documents", "metadatas"])
    documente = corpus["documents"]
    metadate = corpus["metadatas"]
    if not documente:
        return []

    vector = model.encode(intrebare, normalize_embeddings=True).tolist()
    semantic = collection.query(
        query_embeddings=[vector], n_results=min(NUMAR_REZULTATE, len(documente)),
        where=filtru, include=["documents", "metadatas", "distances"],
    )
    pozitii = {(m["source"], m["page"], m["chunk"]): i for i, m in enumerate(metadate)}
    scoruri = {}
    for loc, (meta, distanta) in enumerate(zip(semantic["metadatas"][0], semantic["distances"][0])):
        # O distanță mică înseamnă o potrivire semantică mai bună.
        if distanta <= DISTANTA_MAXIMA:
            i = pozitii[(meta["source"], meta["page"], meta["chunk"])]
            scoruri[i] = 1 / (loc + 1)

    bm25 = index_bm25(tuple(documente))
    lexical = sorted(enumerate(bm25.get_scores(tokenize(intrebare))), key=lambda pereche: pereche[1], reverse=True)
    for loc, (i, scor) in enumerate(lexical[:NUMAR_REZULTATE]):
        if scor > 0:
            # Adunăm punctele clasamentelor, ca în lecția 8.
            scoruri[i] = scoruri.get(i, 0) + 1 / (loc + 1)

    ordine = sorted(scoruri, key=scoruri.get, reverse=True)[:NUMAR_REZULTATE]
    return [{"text": documente[i], **metadate[i]} for i in ordine]
