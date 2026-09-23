import json
import sys
from pathlib import Path

from pydantic import BaseModel, EmailStr, Field


class StudentValidator(BaseModel):
    nume: str
    varsta: int = Field(gt=0, strict=True)  # Doar numere intregi pozitive.
    email: EmailStr


Student = StudentValidator  # Enuntul foloseste ambele nume pentru clasa.


def citeste_student(cale: Path) -> StudentValidator:
    with cale.open(encoding="utf-8") as fisier:
        date = json.load(fisier)
    return Student(**date)  # Trimitem datele din JSON la validare.


if __name__ == "__main__":
    # Putem da alt fisier in comanda; implicit citim student.json.
    cale = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("student.json")
    student = citeste_student(cale)
    print(f"{student.nume}, {student.varsta} ani, {student.email}")
