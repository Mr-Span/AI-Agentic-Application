from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from openai.types.chat import ChatCompletionMessage
from pydantic import ValidationError

from proiect_final import agent, indexare


def test_indexare_metadate_si_reindexare(tmp_path, monkeypatch):
    pymupdf = pytest.importorskip("pymupdf")
    (tmp_path / "note.txt").write_text("a" * 1600, encoding="utf-8")
    with pymupdf.open() as pdf:
        for text in ["First page", "Pagina in romana", "Third page"]:
            pdf.new_page().insert_text((72, 72), text)
        pdf.save(tmp_path / "exemplu.pdf")
    monkeypatch.setattr(indexare, "citeste_catalog", lambda: {
        "documente": [{"fisier": "exemplu.pdf", "pagini_ro": [2, 2]}],
    })

    # O colecție mică în memorie este suficientă pentru acest test.
    class Colectie:
        def __init__(self):
            self.date = {}

        def get(self, **kwargs):
            return {"ids": list(self.date)}

        def delete(self, ids):
            for id_chunk in ids:
                del self.date[id_chunk]

        def upsert(self, ids, documents, metadatas, embeddings):
            self.date.update(zip(ids, metadatas))

    collection = Colectie()
    model = Mock()
    model.encode.side_effect = lambda texte, **kwargs: SimpleNamespace(
        tolist=lambda: [[1.0, 0.0] for _ in texte],
    )
    assert indexare.indexeaza(collection, model, tmp_path) == 4
    assert indexare.indexeaza(collection, model, tmp_path) == 4
    assert len(collection.date) == 4
    assert all(set(meta) == {"source", "page", "chunk"} for meta in collection.date.values())
    assert collection.date["exemplu.pdf:1"] == {"source": "exemplu.pdf", "page": 2, "chunk": 1}
    assert [collection.date[f"note.txt:{i}"]["chunk"] for i in [1, 2, 3]] == [1, 2, 3]
    (tmp_path / "note.txt").unlink()
    assert indexare.indexeaza(collection, model, tmp_path) == 1
    assert len(collection.date) == 1


def test_validare_intrebare_si_context_text():
    for valoare in ["", "   ", 25, None]:
        with pytest.raises(ValidationError):
            agent.IntrebareRAG(question=valoare)
    for valoare in ["", 25, {"context": "text"}]:
        with pytest.raises(ValidationError):
            agent.ContextRAG.model_validate(valoare)
    assert agent.IntrebareRAG(question="  Ce cere garantia?  ").question == "Ce cere garantia?"
    collection, model = Mock(), Mock()
    texte = [f"Manual despre curatarea aparatului. Exemplul {i}." for i in range(11)]
    texte.append("Pentru garantie sunt necesare factura fiscala si certificatul de garantie.")
    metadate = [{"source": f"manual{i}.txt", "page": 1, "chunk": 1} for i in range(11)]
    metadate.append({"source": "garantie.txt", "page": 19, "chunk": 7})
    collection.get.return_value = {"documents": texte, "metadatas": metadate}
    # Căutarea semantică ratează garanția. BM25 trebuie să o recupereze.
    collection.query.return_value = {
        "documents": [texte[:10]], "metadatas": [metadate[:10]], "distances": [[0.2] * 10],
    }
    model.encode.return_value.tolist.return_value = [1.0, 0.0]
    argumente = '{"question":"factura fiscala garantie"}'
    context = agent.rag_search(argumente, collection, model)
    assert isinstance(context, str)
    assert "[garantie.txt, pagina 19, fragment 7]" in context
    assert context.count("fragment ") == 10
    assert collection.query.call_args.kwargs["n_results"] == 10
    assert collection.query.call_args.kwargs["where"] is None

    # Pragul semantic elimină potrivirile slabe; BM25 poate păstra potrivirea exactă.
    collection.query.return_value["distances"] = [[0.9] * 10]
    context = agent.rag_search(argumente, collection, model)
    assert context == "[garantie.txt, pagina 19, fragment 7]\n" + texte[-1]
    assert agent.rag_search('{"question":"zzzxxyy999"}', collection, model) == agent.FARA_REZULTATE

    surse = ["manual.pdf", "garantie.txt"]
    collection.get.return_value = {"documents": texte[-1:], "metadatas": metadate[-1:]}
    collection.query.return_value = {
        "documents": [texte[-1:]], "metadatas": [metadate[-1:]], "distances": [[0.2]],
    }
    agent.rag_search(argumente, collection, model, surse)
    assert collection.query.call_args.kwargs["where"] == {"source": {"$in": surse}}
    assert collection.get.call_args.kwargs["where"] == {"source": {"$in": surse}}
    with pytest.raises(ValidationError):
        agent.rag_search('{"question":25}', collection, model, surse)


def test_agentul_trimite_contextul_in_mesajul_tool(monkeypatch, tmp_path):
    stil = tmp_path / "stil.txt"
    stil.write_text("Raspuns direct, pasi numerotati, surse la final.", encoding="utf-8")
    monkeypatch.setattr(agent, "STIL_RASPUNS", stil)
    apel = ChatCompletionMessage(role="assistant", tool_calls=[{
        "id": "rag_1", "type": "function", "function": {
            "name": "rag_search", "arguments": '{"question":"Ce document este necesar?"}',
        },
    }])
    final = ChatCompletionMessage(role="assistant", content="Dovada achizitiei [garantie.txt, pagina 1].")
    client = Mock()
    client.chat.completions.create.side_effect = [
        SimpleNamespace(choices=[SimpleNamespace(message=apel)]),
        SimpleNamespace(choices=[SimpleNamespace(message=final)]),
    ]
    cautare = Mock(return_value="[garantie.txt, pagina 1, fragment 3]\nEste necesara dovada achizitiei.")
    monkeypatch.setattr(agent, "rag_search", cautare)
    mesaje = [{"role": "user", "content": "Ce document este necesar?"}]
    surse = ["manual.pdf", "garantie.txt"]
    assert agent.raspunde(client, "model-test", mesaje, None, None, surse) == final.content
    cautare.assert_called_once_with('{"question":"Ce document este necesar?"}', None, None, surse)
    assert mesaje[2] == {"role": "tool", "tool_call_id": "rag_1", "content": cautare.return_value}
    assert client.chat.completions.create.call_count == 2
    assert client.chat.completions.create.call_args.kwargs["tool_choice"] == "none"
    instructiuni = client.chat.completions.create.call_args.kwargs["messages"][-1]["content"]
    assert stil.read_text(encoding="utf-8") in instructiuni

    # Dacă serviciul trimite un răspuns gol, afișăm un mesaj clar și în chat.
    stil.write_text("Explica pe intelesul unui incepator.", encoding="utf-8")
    client.chat.completions.create.side_effect = [
        SimpleNamespace(choices=[SimpleNamespace(message=apel)]),
        SimpleNamespace(choices=[SimpleNamespace(message=ChatCompletionMessage(role="assistant", content=None))]),
    ]
    mesaje = [{"role": "user", "content": "Ce document este necesar?"}]
    rezultat = agent.raspunde(client, "model-test", mesaje, None, None, surse)
    assert rezultat == mesaje[-1]["content"]
    assert "Incearca din nou" in rezultat
    assert "Explica pe intelesul unui incepator." in client.chat.completions.create.call_args.kwargs["messages"][-1]["content"]

    # Ramura fără rezultate se încheie fără al doilea apel LLM.
    client.reset_mock()
    client.chat.completions.create.side_effect = [SimpleNamespace(choices=[SimpleNamespace(message=apel)])]
    cautare.return_value = agent.FARA_REZULTATE
    mesaje = [{"role": "user", "content": "Ce document este necesar?"}]
    assert agent.raspunde(client, "model-test", mesaje, None, None) == agent.FARA_REZULTATE
    assert client.chat.completions.create.call_count == 1
    assert mesaje[-2]["role"] == "tool"
    assert mesaje[-1]["content"] == agent.FARA_REZULTATE
