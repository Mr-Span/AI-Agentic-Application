from pathlib import Path

from tema_1 import citeste_student


def test_student():
    cale = Path(__file__).resolve().parents[1] / "student.json"
    student = citeste_student(cale)
    assert student.nume == "Ana Popescu"
    assert student.varsta == 20
    assert student.email == "ana.popescu@example.com"
