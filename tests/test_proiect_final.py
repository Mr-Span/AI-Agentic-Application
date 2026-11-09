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
    collection.count.return_value = 12
    collection.get.return_value = {"ids": list(range(12))}
    collection.query.return_value = {
        "documents": [["Este necesara dovada achizitiei."]],
        "metadatas": [[{"source": "garantie.txt", "page": 1, "chunk": 3}]],
    }
    model.encode.return_value.tolist.return_value = [1.0, 0.0]
    surse = ["manual.pdf", "garantie.txt"]
    context = agent.rag_search('{"question":"Ce document este necesar?"}', collection, model, surse)
    assert isinstance(context, str)
    assert context == "[garantie.txt, pagina 1, fragment 3]\nEste necesara dovada achizitiei."
    assert collection.query.call_args.kwargs["n_results"] == 10
    assert collection.query.call_args.kwargs["where"] == {"source": {"$in": surse}}
    with pytest.raises(ValidationError):
        agent.rag_search('{"question":25}', collection, model, surse)


def test_agentul_trimite_contextul_in_mesajul_tool(monkeypatch):
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
