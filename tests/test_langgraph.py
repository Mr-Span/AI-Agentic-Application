from unittest.mock import Mock

import pytest

import lesson_09_langgraph as lectie


def test_graful_cu_erori():
    pytest.importorskip("langgraph")
    result = lectie.build_graph().invoke(lectie.State(log_file="log_report.txt"))
    assert len(result["errors"]) == 2
    assert result["response"] == "Simulare: incident pentru 2 erori."


def test_graful_fara_erori_nu_apeleaza_incidentul(monkeypatch):
    pytest.importorskip("langgraph")

    def incident_neasteptat(state):
        raise AssertionError("Raportul fara erori nu trebuie sa ajunga aici.")

    monkeypatch.setattr(lectie, "call_incident_api", incident_neasteptat)
    result = lectie.build_graph().invoke(lectie.State(log_file="log_report_ok.txt"))
    assert result["errors"] == []
    assert result["response"] == "Nu sunt erori in log."


def test_error_din_mesaj_nu_este_nivel_de_log(tmp_path, monkeypatch):
    monkeypatch.setattr(lectie, "PROJECT_ROOT", tmp_path)
    (tmp_path / "test.txt").write_text(
        "2026-10-22 10:00:00 INFO  No ERROR found\n"
        "2026-10-22 10:01:00 ERROR Connection failed\n", encoding="utf-8",
    )
    result = lectie.read_log_report(lectie.State(log_file="test.txt"))
    assert result["errors"] == ["2026-10-22 10:01:00 ERROR Connection failed"]


@pytest.mark.parametrize("nume", ["../secret.txt", ".env", "info.json"])
def test_raportul_trebuie_sa_fie_text_din_proiect(nume):
    with pytest.raises(ValueError):
        lectie.read_log_report(lectie.State(log_file=nume))


def test_api_demo_primeste_numarul_de_erori(monkeypatch):
    requests = pytest.importorskip("requests")
    response = Mock(status_code=201)
    post = Mock(return_value=response)
    monkeypatch.setattr(requests, "post", post)
    state = lectie.State(errors=["eroare 1", "eroare 2"], simulate_api=False)
    result = lectie.call_incident_api(state)
    assert "HTTP 201" in result["response"]
    assert post.call_args.args == (lectie.INCIDENT_API,)
    assert post.call_args.kwargs["json"]["title"] == "Raport de curs: 2 erori"
    assert post.call_args.kwargs["timeout"] == 15
    response.raise_for_status.assert_called_once()


def test_api_indisponibil_nu_opreste_programul(monkeypatch):
    requests = pytest.importorskip("requests")
    monkeypatch.setattr(requests, "post", Mock(side_effect=requests.Timeout))
    result = lectie.call_incident_api(lectie.State(errors=["eroare"], simulate_api=False))
    assert "nu a raspuns corect" in result["response"]
