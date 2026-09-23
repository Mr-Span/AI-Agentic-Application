"""Teste pentru traseul complet: fișier JSON → citire → validare."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tema_1 import StudentValidator, citeste_student


def test_student_din_fisierul_real():
    """Datele din fișierul predat trebuie citite și validate corect."""
    cale = Path(__file__).resolve().parents[1] / "student.json"
    student = citeste_student(cale)

    # assert verifică o condiție; o condiție falsă face testul să eșueze.
    assert isinstance(student, StudentValidator)
    assert student.nume == "Ana Popescu"
    assert student.varsta == 20
    assert student.email == "ana.popescu@example.com"


@pytest.mark.parametrize(
    "camp, valoare",
    [
        ("email", "email-invalid"),
        ("varsta", 0),
        ("varsta", -1),
        ("varsta", "20"),
        ("varsta", 20.0),
        ("varsta", True),
        ("nume", 123),
    ],
)
def test_date_invalide(tmp_path, camp, valoare):
    """Aceeași verificare este rulată separat pentru fiecare exemplu invalid."""
    date = {"nume": "Ana Popescu", "varsta": 20, "email": "ana.popescu@example.com"}
    date[camp] = valoare
    # tmp_path este un folder temporar oferit de pytest: nu modificăm tema reală.
    cale = tmp_path / "student.json"
    cale.write_text(json.dumps(date), encoding="utf-8")

    # Aici eroarea este rezultatul așteptat: datele incorecte trebuie respinse.
    with pytest.raises(ValidationError) as eroare:
        citeste_student(cale)
    assert eroare.value.errors()[0]["loc"] == (camp,)


@pytest.mark.parametrize("camp", ["nume", "varsta", "email"])
def test_camp_obligatoriu_lipsa(tmp_path, camp):
    """Niciunul dintre cele trei câmpuri nu poate lipsi."""
    date = {"nume": "Ana Popescu", "varsta": 20, "email": "ana.popescu@example.com"}
    del date[camp]
    cale = tmp_path / "student.json"
    cale.write_text(json.dumps(date), encoding="utf-8")

    with pytest.raises(ValidationError) as eroare:
        citeste_student(cale)
    assert eroare.value.errors()[0]["loc"] == (camp,)
    assert eroare.value.errors()[0]["type"] == "missing"


def test_json_incorect(tmp_path):
    """Un JSON incomplet eșuează la citire, înainte de validarea Pydantic."""
    cale = tmp_path / "student.json"
    cale.write_text('{"nume":', encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        citeste_student(cale)


def test_fisier_inexistent(tmp_path):
    """Lipsa fișierului rămâne vizibilă pentru codul care apelează funcția."""
    with pytest.raises(FileNotFoundError):
        citeste_student(tmp_path / "inexistent.json")
