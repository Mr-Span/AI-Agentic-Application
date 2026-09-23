"""Tema 1: citim un fișier JSON și verificăm datele cu Pydantic."""

import json  # Modul inclus în Python: transformă JSON-ul în obiecte Python.
from pathlib import Path  # Construiește căi către fișiere, inclusiv pe Windows.

from pydantic import BaseModel, EmailStr, Field


class StudentValidator(BaseModel):
    """Descrie câmpurile obligatorii și regulile pentru un student."""

    # BaseModel verifică automat datele când construim un obiect din această clasă.
    nume: str
    # gt=0 înseamnă „mai mare decât zero”. strict=True cere chiar un întreg:
    # respinge inclusiv textul "20", numărul 20.0 și valorile True/False.
    varsta: int = Field(gt=0, strict=True)
    # EmailStr verifică formatul adresei; nu dovedește că acea căsuță poștală există.
    email: EmailStr


# Enunțul cere atât numele StudentValidator, cât și Student.
# Un alias este un al doilea nume pentru aceeași clasă, fără reguli duplicate.
Student = StudentValidator


def citeste_student(cale: Path) -> StudentValidator:
    """Citește JSON-ul și întoarce studentul validat sau propagă eroarea întâlnită."""
    # „with” închide automat fișierul; UTF-8 permite și caractere românești.
    with cale.open("r", encoding="utf-8") as fisier:
        date = json.load(fisier)

    # JSON-ul a devenit un dicționar. **date trimite fiecare pereche cheie-valoare
    # ca argument: Student(nume="Ana Popescu", varsta=20, email="...").
    # Dacă o regulă nu este respectată, Pydantic ridică ValidationError.
    return Student(**date)


if __name__ == "__main__":
    # Blocul rulează doar la executarea scriptului, nu când îl importă testele.
    # __file__ este calea acestui script, deci nu depindem de folderul terminalului.
    cale_json = Path(__file__).resolve().parent / "student.json"
    student = citeste_student(cale_json)
    print("Student validat cu succes:")
    print(f"Nume: {student.nume}")
    print(f"Varsta: {student.varsta}")
    print(f"Email: {student.email}")
