from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from openai.types.chat import ChatCompletionMessage
from pydantic import ValidationError

pytest.importorskip("langgraph")
import lesson_10_langgraph as lectie


def test_demo_pastreaza_istoricul_si_raporteaza_o_data():
    rezultat = lectie.build_graph().invoke(lectie.State(demo=True))
    assert len(rezultat["errors"]) == 2
    assert rezultat["agent_steps"] == 2
    assert rezultat["incident_created"] is True
    mesaje = rezultat["messages"]
    assert [m["role"] for m in mesaje] == ["system", "user", "assistant", "tool", "assistant"]
    assert mesaje[3]["tool_call_id"] == mesaje[2]["tool_calls"][0]["id"]
    assert rezultat["response"] == "Incident simulat pentru 2 erori."


def test_fara_erori_nu_se_apeleaza_llm():
    client = Mock()
    rezultat = lectie.build_graph(client, "model-test").invoke(
        lectie.State(log_file="log_report_ok.txt"),
    )
    assert rezultat["response"] == "Nu sunt erori in log."
    assert rezultat["agent_steps"] == 0
    client.chat.completions.create.assert_not_called()


def test_validare_limita_si_incident_fara_duplicate(monkeypatch):
    with pytest.raises(ValidationError):
        lectie.create_incident({"title": "Eroare", "summary": "Un timeout.", "severity_level": "urgent"})
    monkeypatch.setattr(lectie, "MAX_AGENT_STEPS", 3)
    client = Mock()
    # Modelul simulat insistă cu aceeași unealtă; codul trebuie să îl oprească.
    raspunsuri = []
    for numar in range(3):
        mesaj = ChatCompletionMessage(role="assistant", tool_calls=[{
            "id": f"incident_{numar}", "type": "function", "function": {
                "name": "create_incident",
                "arguments": '{"title":"Timeout","summary":"Erori de plata.","severity_level":"medium"}',
            },
        }])
        raspunsuri.append(SimpleNamespace(choices=[SimpleNamespace(message=mesaj)]))
    client.chat.completions.create.side_effect = raspunsuri
    rezultat = lectie.build_graph(client, "model-test").invoke(lectie.State())
    assert client.chat.completions.create.call_count == 3
    assert "limita de pasi" in rezultat["response"]
    unelte = [m for m in rezultat["messages"] if m["role"] == "tool"]
    assert len(unelte) == 2 and "deja raportat" in unelte[1]["content"]
    assert client.chat.completions.create.call_args.kwargs["tool_choice"] == "none"
