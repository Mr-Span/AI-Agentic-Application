from unittest.mock import Mock

from tema_3_1 import afiseaza_raspuns, cauta
from tema_3_2 import filtreaza_distanta
from tema_3_optionala import reordoneaza


def test_cautare_doar_in_sursa_aleasa():
    collection, model = Mock(), Mock()
    collection.get.return_value = {"ids": ["1"]}
    model.encode.return_value.tolist.return_value = [1.0, 0.0]
    collection.query.return_value = {
        "documents": [["Marcus reads a book."]],
        "metadatas": [[{"source": "paragraphs.txt", "page": 1}]],
        "distances": [[0.2]],
    }
    rezultate = cauta(collection, model, "paragraphs.txt", "Who reads?")
    assert collection.query.call_args.kwargs["where"] == {"source": "paragraphs.txt"}
    assert collection.query.call_args.kwargs["n_results"] == 3
    assert rezultate[0]["page"] == 1
    cauta(collection, model, "paragraphs.txt", "Who reads?", nr_rezultate=15)
    assert collection.query.call_args.kwargs["n_results"] == 15


def test_distanta_si_lipsa_rezultatelor():
    rezultate = [{"distance": 0.2}, {"distance": 0.5}, {"distance": 0.51}]
    assert filtreaza_distanta(rezultate) == rezultate[:2]
    client = Mock()
    afiseaza_raspuns(client, "intrebare", filtreaza_distanta([rezultate[2]]))
    client.chat.completions.create.assert_not_called()


def test_reranking_top_patru_si_scor_mic():
    rezultate = [{"text": f"fragment {i}", "source": "a.txt", "page": 1} for i in range(6)]
    reranker = Mock()
    reranker.predict.return_value = [0.1, 0.6, 0.9, 0.8, 0.7, 0.5]
    alese = reordoneaza("intrebare", rezultate, reranker)
    assert [rezultat["score"] for rezultat in alese] == [0.9, 0.8, 0.7, 0.6]
    reranker.predict.return_value = [0.1] * 6
    client = Mock()
    afiseaza_raspuns(client, "intrebare", reordoneaza("intrebare", rezultate, reranker))
    client.chat.completions.create.assert_not_called()
