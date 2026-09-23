from types import SimpleNamespace
from unittest.mock import Mock

from openai.types.chat import ChatCompletionMessage

import tema2


def test_unelte():
    assert "student.json" in tema2.listeaza_fisiere({})
    assert "pyproject.toml" in tema2.cauta_cuvant({"cuvant": "pytest"})


def test_cautare_in_subfolder(tmp_path, monkeypatch):
    monkeypatch.setattr(tema2, "PROIECT", tmp_path)
    (tmp_path / "exemple").mkdir()
    (tmp_path / "exemple" / "test.txt").write_text("PYTEST", encoding="utf-8")
    (tmp_path / "gol.txt").write_text("alt text", encoding="utf-8")
    (tmp_path / ".env").write_text("API_KEY=pytest", encoding="utf-8")
    assert tema2.cauta_cuvant({}) == "exemple/test.txt"
    assert ".env" not in tema2.listeaza_fisiere({})


def test_agent():
    # Simulam doar LLM-ul; uneltele citesc fisierele reale, fara cheie API.
    client = Mock()
    apeluri = []

    def raspunde(**cerere):
        alegere = cerere["tool_choice"]
        if alegere == "none":
            rezultate = [m for m in cerere["messages"] if m["role"] == "tool"]
            assert "student.json" in rezultate[0]["content"]
            mesaj = ChatCompletionMessage(role="assistant", content=rezultate[1]["content"])
        else:
            nume = alegere["function"]["name"]
            apeluri.append(nume)
            argumente = '{"cuvant": "pytest"}' if nume == "cauta_cuvant" else "{}"
            mesaj = ChatCompletionMessage(role="assistant", tool_calls=[{
                "id": nume, "type": "function",
                "function": {"name": nume, "arguments": argumente},
            }])
        return SimpleNamespace(choices=[SimpleNamespace(message=mesaj)])

    client.chat.completions.create.side_effect = raspunde
    rezultat = tema2.ruleaza_agent(client, "model-test")
    assert apeluri == ["listeaza_fisiere", "cauta_cuvant"]
    assert "pyproject.toml" in rezultat
    assert client.chat.completions.create.call_count == 3
