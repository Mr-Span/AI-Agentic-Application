import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from openai.types.chat import ChatCompletionMessage

import lesson_08_semantic_search as lectie


def corpus_de_test():
    documents = ["A traveller explores distant stars.", "Invoice INV-2026-003 is unpaid.", "Fresh bread and cheese."]
    metadatas = [
        {"source": "StarMaker.pdf", "page": 1, "chunk": 0},
        {"source": "invoices.pdf", "page": 2, "chunk": 0},
        {"source": "invoices.pdf", "page": 3, "chunk": 0},
    ]
    collection = Mock()
    collection.count.return_value = 3
    collection.query.return_value = {"metadatas": [[metadatas[0], metadatas[1], metadatas[2]]]}
    model = Mock()
    model.encode.return_value.tolist.return_value = [1.0, 0.0]
    return collection, model, documents, metadatas


def test_bm25_ridica_factura_cu_codul_cautat():
    rank_bm25 = pytest.importorskip("rank_bm25")
    collection, model, documents, metadatas = corpus_de_test()
    bm25 = rank_bm25.BM25Okapi([lectie.tokenize(doc) for doc in documents])
    results = lectie.hybrid_search(collection, model, bm25, documents, metadatas,
                                   json.dumps({"question": "INV-2026-003"}))
    assert "INV-2026-003" in results[0]
    assert "[invoices.pdf, pagina 2]" in results[0]
    # Un PDF vechi din bază nu trebuie să intre în căutarea de acum.
    criteriu = collection.query.call_args.kwargs["where"]
    assert set(criteriu["source"]["$in"]) == {"StarMaker.pdf", "invoices.pdf"}


def test_scorurile_zero_nu_adauga_fragmente_la_intamplare():
    collection, model, documents, metadatas = corpus_de_test()
    collection.query.return_value = {"metadatas": [[metadatas[0]]]}
    bm25 = Mock()
    bm25.get_scores.return_value = [0, 0, 0]
    results = lectie.hybrid_search(collection, model, bm25, documents, metadatas,
                                   '{"question":"cosmos"}')
    assert len(results) == 1
    assert "StarMaker.pdf" in results[0]


@pytest.mark.parametrize("args", ['{"question":"   "}', '{"other":"test"}', 'nu este JSON'])
def test_argumente_invalide(args):
    with pytest.raises(ValueError):
        lectie.hybrid_search(None, None, None, [], [], args)


def test_baza_goala_nu_cere_embedding():
    collection = Mock()
    collection.count.return_value = 0
    model = Mock()
    result = lectie.search_document(collection, model, "ceva", "carte.pdf")
    assert result["documents"] == [[]]
    model.encode.assert_not_called()


def test_agentul_cauta_inainte_sa_formuleze_raspunsul(monkeypatch):
    apel = ChatCompletionMessage(role="assistant", tool_calls=[{
        "id": "cautare_1", "type": "function", "function": {
            "name": "search_starmaker", "arguments": '{"question":"Ce factura este neplatita?"}',
        },
    }])
    rezumat = ChatCompletionMessage(role="assistant", content="Factura este neplatita [invoices.pdf, pagina 2].")
    final = ChatCompletionMessage(role="assistant", content=rezumat.content)
    client = Mock()
    client.chat.completions.create.side_effect = [
        SimpleNamespace(choices=[SimpleNamespace(message=mesaj)]) for mesaj in [apel, rezumat, final]
    ]
    cautare = Mock(return_value=["[invoices.pdf, pagina 2]\nFactura neplatita."])
    monkeypatch.setattr(lectie, "hybrid_search", cautare)
    messages = [{"role": "user", "content": "Ce factura este neplatita?"}]
    result = lectie.raspunde_agent(client, messages, None, None, None, [], [])
    assert result == final.content
    cautare.assert_called_once()
    assert messages[2]["tool_call_id"] == "cautare_1"
    assert "[invoices.pdf, pagina 2]" in messages[2]["content"]
    assert client.chat.completions.create.call_args.kwargs["tool_choice"] == "none"


def test_conversatia_obisnuita_nu_lanseaza_cautarea(monkeypatch):
    client = Mock()
    client.chat.completions.create.return_value = SimpleNamespace(choices=[
        SimpleNamespace(message=ChatCompletionMessage(role="assistant", content="Salut!")),
    ])
    cautare = Mock()
    monkeypatch.setattr(lectie, "hybrid_search", cautare)
    assert lectie.raspunde_agent(client, [{"role": "user", "content": "Salut"}],
                                 None, None, None, [], []) == "Salut!"
    cautare.assert_not_called()


def test_unealta_returneaza_eroare_pentru_argumente_gresite():
    client = Mock()
    apel = ChatCompletionMessage(role="assistant", tool_calls=[{
        "id": "gresit_1", "type": "function", "function": {
            "name": "search_starmaker", "arguments": '{"question":""}',
        },
    }])
    client.chat.completions.create.side_effect = [
        SimpleNamespace(choices=[SimpleNamespace(message=apel)]),
        SimpleNamespace(choices=[SimpleNamespace(message=ChatCompletionMessage(role="assistant", content="Reformuleaza."))]),
    ]
    messages = [{"role": "user", "content": "cauta"}]
    lectie.raspunde_agent(client, messages, None, None, None, [], [])
    assert messages[2]["content"].startswith("Eroare:")
