import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from openai.types.chat import ChatCompletionMessage

import lesson_06_simplest_agent as agent
from workshop_cuvinte import raport_cautare


def test_raport_marcus():
    raport = raport_cautare("marcus")
    assert "Word found : 8 times" in raport
    assert "File total word count: 51 words." in raport


def test_cuvinte_intregi_si_punctuatie(tmp_path):
    cale = tmp_path / "text.txt"
    cale.write_text("Marcus, MARCUS! marcus123 demarcus.", encoding="utf-8")
    assert "Word found : 2 times" in raport_cautare("Marcus", cale)


def test_analiza_document():
    raport = json.loads(agent.analyze_document({
        "file_name": "paragraphs.txt", "words": ["marcus", "Marcus", "absent"],
    }))
    assert raport["word_count"] == 51
    assert raport["matches"] == {"marcus": 8, "Marcus": 8, "absent": 0}


@pytest.mark.parametrize("nume", [".env", "../secret.txt", ".git/config"])
def test_fisiere_restrictionate(nume):
    with pytest.raises(ValueError):
        agent.citeste_fisier(nume)


def test_ruleaza_un_test_real():
    rezultat = agent.run_tests({"tests": ["tests/test_tema_1.py"]})
    assert "Cod iesire: 0" in rezultat
    assert "1 passed" in rezultat


def test_respingere_optiuni_pytest():
    assert agent.run_tests({"tests": ["--help"]}).startswith("Eroare:")


def test_rezumat_validat():
    client = Mock()
    mesaj = SimpleNamespace(content='{"title":"Marcus","summary":"O intalnire."}')
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=mesaj)],
    )
    rezultat = json.loads(agent.summarize_file(client, {"name": "paragraphs.txt"}))
    assert rezultat["title"] == "Marcus"
    mesaj.content = '{"title":"Lipseste rezumatul"}'
    assert agent.summarize_file(client, {"name": "paragraphs.txt"}).startswith("Eroare:")


def test_agent_trimite_rezultatul_uneltei():
    client = Mock()
    apel = ChatCompletionMessage(role="assistant", content=None, tool_calls=[{
        "id": "apel_1", "type": "function", "function": {
            "name": "analyze_document",
            "arguments": '{"file_name":"paragraphs.txt","words":["marcus"]}',
        },
    }])
    final = ChatCompletionMessage(role="assistant", content="Marcus apare de 8 ori.")
    client.chat.completions.create.side_effect = [
        SimpleNamespace(choices=[SimpleNamespace(message=apel)]),
        SimpleNamespace(choices=[SimpleNamespace(message=final)]),
    ]
    mesaje = [{"role": "user", "content": "Numara marcus in paragraphs.txt"}]
    assert agent.raspunde(client, mesaje, agent.unelte_agent()) == final.content
    rezultat = mesaje[2]
    assert rezultat["tool_call_id"] == "apel_1"
    assert json.loads(rezultat["content"])["matches"]["marcus"] == 8
    assert client.chat.completions.create.call_args.kwargs["tool_choice"] == "none"
