from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from openai.types.chat import ChatCompletionMessage
from pydantic import ValidationError

from proiect_final import agent, indexare


def test_indexare_metadate_si_reindexare(tmp_path):
    pymupdf = pytest.importorskip("pymupdf")
    (tmp_path / "note.txt").write_text("a" * 1600, encoding="utf-8")
    with pymupdf.open() as pdf:
        for text in ["Prima pagina", "A doua pagina"]:
            pdf.new_page().insert_text((72, 72), text)
        pdf.save(tmp_path / "exemplu.pdf")

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
    assert indexare.indexeaza(collection, model, tmp_path) == 5
    assert indexare.indexeaza(collection, model, tmp_path) == 5
    assert len(collection.date) == 5
    assert all(set(meta) == {"source", "page", "chunk"} for meta in collection.date.values())
    assert {meta["page"] for meta in collection.date.values() if meta["source"] == "exemplu.pdf"} == {1, 2}
    assert [collection.date[f"note.txt:{i}"]["chunk"] for i in [1, 2, 3]] == [1, 2, 3]
    (tmp_path / "note.txt").unlink()
    assert indexare.indexeaza(collection, model, tmp_path) == 2
    assert len(collection.date) == 2


def test_validare_intrebare_si_context_text():
    for valoare in ["", "   ", 25, None]:
        with pytest.raises(ValidationError):
            agent.IntrebareRAG(question=valoare)
    for valoare in ["", 25, {"context": "text"}]:
        with pytest.raises(ValidationError):
            agent.ContextRAG.model_validate(valoare)
    assert agent.IntrebareRAG(question="  Cine este Marcus?  ").question == "Cine este Marcus?"
    collection, model = Mock(), Mock()
    collection.count.return_value = 12
    collection.query.return_value = {
        "documents": [["Marcus citeste."]],
        "metadatas": [[{"source": "note.txt", "page": 2, "chunk": 3}]],
    }
    model.encode.return_value.tolist.return_value = [1.0, 0.0]
    context = agent.rag_search('{"question":"Cine citeste?"}', collection, model)
    assert isinstance(context, str)
    assert context == "[note.txt, pagina 2, fragment 3]\nMarcus citeste."
    assert collection.query.call_args.kwargs["n_results"] == 10


def test_agentul_trimite_contextul_in_mesajul_tool(monkeypatch):
    apel = ChatCompletionMessage(role="assistant", tool_calls=[{
        "id": "rag_1", "type": "function", "function": {
            "name": "rag_search", "arguments": '{"question":"Cine citeste?"}',
        },
    }])
    final = ChatCompletionMessage(role="assistant", content="Marcus citeste [note.txt, pagina 2].")
    client = Mock()
    client.chat.completions.create.side_effect = [
        SimpleNamespace(choices=[SimpleNamespace(message=apel)]),
        SimpleNamespace(choices=[SimpleNamespace(message=final)]),
    ]
    cautare = Mock(return_value="[note.txt, pagina 2, fragment 3]\nMarcus citeste.")
    monkeypatch.setattr(agent, "rag_search", cautare)
    mesaje = [{"role": "user", "content": "Cine citeste?"}]
    assert agent.raspunde(client, "model-test", mesaje, None, None) == final.content
    assert mesaje[2] == {"role": "tool", "tool_call_id": "rag_1", "content": cautare.return_value}
    assert client.chat.completions.create.call_count == 2
    assert client.chat.completions.create.call_args.kwargs["tool_choice"] == "none"
