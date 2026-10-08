from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import lesson_08_semantic_search as lectie


def test_bucati_cu_suprapunere():
    # Caractere diferite, ca să verificăm că porțiunea comună e cea corectă.
    text = "".join(chr(0x4E00 + i) for i in range(1600))
    chunks = lectie.chunk_text(text)
    assert [len(chunk) for chunk in chunks] == [800, 800, 240]
    assert chunks[0][-120:] == chunks[1][:120]
    assert chunks[1][-120:] == chunks[2][:120]
    assert chunks[0] + chunks[1][120:] + chunks[2][120:] == text


def test_text_gol():
    assert lectie.chunk_text("   \n") == []


def test_suprapunere_invalida(monkeypatch):
    # Dacă pasul ar fi 0, bucla nu s-ar mai termina.
    monkeypatch.setattr(lectie, "CHUNK_OVERLAP", lectie.CHUNK_SIZE)
    with pytest.raises(ValueError):
        lectie.chunk_text("exemplu")


def test_context_cu_pagini():
    rezultat = {
        "documents": [["Primul fragment", "Al doilea fragment"]],
        "metadatas": [[{"source": "carte.pdf", "page": 3}, {"source": "carte.pdf", "page": 7}]],
    }
    context = lectie.context_din_rezultate(rezultat)
    assert "[carte.pdf, pagina 3]\nPrimul fragment" in context
    assert "[carte.pdf, pagina 7]\nAl doilea fragment" in context


def test_raspuns_foloseste_fragmente_si_surse(monkeypatch):
    # Simulăm doar API-ul; testul nu folosește cheia și nu consumă credit.
    monkeypatch.setenv("MODEL", "model-de-test")
    client = Mock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="Raspuns [carte.pdf, pagina 3]"))],
    )
    rezultat = {"documents": [["Un fragment"]], "metadatas": [[{"source": "carte.pdf", "page": 3}]]}
    raspuns = lectie.answer_with_context(client, "Ce spune cartea?", rezultat)
    cerere = client.chat.completions.create.call_args.kwargs
    assert raspuns == "Raspuns [carte.pdf, pagina 3]"
    assert cerere["model"] == "model-de-test"
    assert "[carte.pdf, pagina 3]" in cerere["messages"][1]["content"]
    assert "Ce spune cartea?" in cerere["messages"][1]["content"]


def test_context_gol_nu_apeleaza_modelul():
    client = Mock()
    rezultat = {"documents": [[]], "metadatas": [[]]}
    assert lectie.answer_with_context(client, "Intrebare", rezultat).startswith("Nu am gasit")
    client.chat.completions.create.assert_not_called()
