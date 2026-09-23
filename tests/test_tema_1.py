from pathlib import Path

import pytest
from pydantic import ValidationError

from tema_1 import Student, citeste_student


@pytest.mark.parametrize("fisier, nume, varsta, email", [
    ("student.json", "Ana Popescu", 20, "ana.popescu@example.com"),
    ("exemple/mihai.json", "Mihai Ionescu", 22, "mihai.ionescu@example.com"),
    ("exemple/elena.json", "Elena Radu", 19, "elena.radu@example.com"),
    ("exemple/andrei.json", "Andrei Stan", 24, "andrei.stan@example.com"),
])
def test_citire_si_validare(fisier, nume, varsta, email):
    # Verificam citirea din JSON si toate valorile studentului.
    student = citeste_student(Path(__file__).resolve().parents[1] / fisier)
    assert isinstance(student, Student)
    assert student.nume == nume
    assert student.varsta == varsta
    assert student.email == email


@pytest.mark.parametrize("varsta, email", [
    (20, "email-gresit"),
    (0, "ana.popescu@example.com"),
    (-1, "ana.popescu@example.com"),
])
def test_date_invalide(varsta, email):
    # Emailul gresit si varsta nepozitiva trebuie respinse.
    with pytest.raises(ValidationError):
        Student(nume="Ana Popescu", varsta=varsta, email=email)
