# Strategia Retrieve & Re-Rank este explicată, cu sursa online, în README.
from tema_3_1 import CACHE, afiseaza_raspuns, cauta, cere_intrebare, pregateste
from tema_3_2 import filtreaza_distanta

MODEL_RERANKING = "cross-encoder/ms-marco-MiniLM-L6-v2"
SCOR_MINIM = 0.5


def reordoneaza(intrebare, rezultate, reranker):
    if not rezultate:
        return []
    # CrossEncoder citește împreună întrebarea și fiecare fragment.
    perechi = [(intrebare, rezultat["text"]) for rezultat in rezultate]
    scoruri = reranker.predict(perechi)
    relevante = []
    for rezultat, scor in zip(rezultate, scoruri):
        if float(scor) >= SCOR_MINIM:
            relevante.append({**rezultat, "score": float(scor)})
    relevante.sort(key=lambda rezultat: rezultat["score"], reverse=True)
    return relevante[:4]  # Doar primele patru ajung la LLM.


def main():
    collection, model, client = pregateste()
    import torch
    from sentence_transformers import CrossEncoder

    # Sigmoid aduce scorurile între 0 și 1. Un scor mai mare este mai bun.
    reranker = CrossEncoder(MODEL_RERANKING, device="cpu", cache_folder=str(CACHE),
                            activation_fn=torch.nn.Sigmoid())
    while True:
        cerere = cere_intrebare()
        if cerere is None:
            break
        sursa, intrebare = cerere
        rezultate = cauta(collection, model, sursa, intrebare, nr_rezultate=15)
        rezultate = filtreaza_distanta(rezultate)
        rezultate = reordoneaza(intrebare, rezultate, reranker)
        afiseaza_raspuns(client, intrebare, rezultate)


if __name__ == "__main__":
    main()
